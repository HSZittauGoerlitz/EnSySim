// external
use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use numpy::PyReadonlyArrayDyn;
use num_integer::Integer;
use log::error;
use rand::prelude::*;

// local
// Entities
#[macro_use]
mod agent;
mod building;
mod cell;
mod sep_bsl_agent;
// Additional
mod components;
mod misc;
mod thermal_systems;


#[pymodule]
fn SystemComponentsFast(_py: Python<'_>, m: &PyModule) -> PyResult<()> {

    pyo3_log::init();

    m.add_class::<agent::Agent>()?;
    m.add_class::<building::Building>()?;
    m.add_class::<cell::Cell>()?;
    m.add_class::<sep_bsl_agent::SepBSLagent>()?;
    m.add_class::<components::boiler::Boiler>()?;
    m.add_class::<components::chp::CHP>()?;
    m.add_class::<components::pv::PV>()?;
    m.add_class::<thermal_systems::building
                  ::heatpump_system::BuildingHeatpumpSystem>()?;
    m.add_class::<thermal_systems::building
                  ::chp_system::BuildingChpSystem>()?;
    m.add_class::<components::generic_storage::GenericStorage>()?;
    m.add_class::<thermal_systems::cell
                  ::chp_system_thermal::CellChpSystemThermal>()?;
    m.add_class::<thermal_systems::cell::theresa_system::TheresaSystem>()?;
    m.add_function(wrap_pyfunction!(simulate, m)?).unwrap();
    m.add_function(wrap_pyfunction!(test_generic_storage, m)?).unwrap();
    m.add_class::<EnSySimEnv>()?;
    Ok(())


}

/// Run Simulation with given models main cell
///
/// # Arguments
/// * main_cell (Cell): Main cell of energy system model
/// * steps (usize): Number of simulation steps to execute
/// * slp_data (HashMap<&str, Vec<f32>>): Standard load profile data for
///     - "PHH": phh agents
///     - "BSLa": agriculture business agents
///     - "BSLc": common business agents
/// * hot_water_data (pyArr<f32>): Actual hot water day profile factors [-]
/// * env_data (HashMap<&str, Vec<f32>>): All Environment/Weather data needed
///     for the simulation
/// * sol_data (HashMap<&str, Vec<f32>>): Elevation and azimut of sun
#[pyfunction]
fn simulate(main_cell: &mut cell::Cell, steps: usize,
            slp_data: HashMap<&str, Vec<f32>>,
            hot_water_data: PyReadonlyArrayDyn<f32>,
            env_data: HashMap<&str, Vec<f32>>,
            sol_data: HashMap<&str, Vec<f32>>) {
    let mut slp: [f32; 3] = [0.; 3];
    let slp_phh = slp_data.get("PHH").unwrap();
    let slp_bsla = slp_data.get("BSLa").unwrap();
    let slp_bslc = slp_data.get("BSLc").unwrap();
    let hot_water_data = hot_water_data.as_array();
    // Get Environment data and create object
    let mut amb = misc::ambient::AmbientParameters::new(0., 0., 0., 0., 0., 0.);
    let t = env_data.get("T [degC]").unwrap();
    let e_global = env_data.get("Eg [W/m^2]").unwrap();
    let e_diffuse = env_data.get("E diffuse [W/m^2]").unwrap();
    let e_direct = env_data.get("E direct [W/m^2]").unwrap();
    let e_elevation = sol_data.get("elevation [degree]").unwrap();
    let e_azimuth = sol_data.get("azimuth [degree]").unwrap();

    // get the constant to a new memory place,
    //since cell can be changed due saving history
    let cell_t_out_n: f32 = main_cell.t_out_n;

    for step in 0..steps {
        // set data for actual step
        // SLP
        slp[0] = slp_phh[step];
        slp[1] = slp_bsla[step];
        slp[2] = slp_bslc[step];

        // Environment
        amb.t_out = t[step];
        let idx_day = step.div_floor(& 96);
        let slice_day = &t[idx_day*96..idx_day*96+95];
        
        amb.t_mean_day = slice_day.iter().sum::<f32>() / slice_day.len() as f32;
        amb.irradiation_glob = e_global[step];
        amb.irradiation_diff = e_diffuse[step];
        amb.irradiation_dir = e_direct[step];
        amb.solar_elevation = e_elevation[step];
        amb.solar_azimuth = e_azimuth[step];
        main_cell.step(&slp, &hot_water_data[step], &cell_t_out_n, &mut amb);
    }
}


/// Test charge / discharge of generic storage
///
/// This function is used, to check that the energy balance is sustained
/// during charging / discharging.
///
/// # Arguments
/// * storage (&GenericStorage): Storage used for test
/// * pow (f32): Charge (positive) / Discharge (negative) power [W]
///
/// # Returns
/// * (f32, f32):
///   - Not received or delivered power [W], difference between
///     requested and handled power
///   - Losses due charging/discharging as well as self discharge [W]
#[pyfunction]
pub fn test_generic_storage(
    storage: &mut components::generic_storage::GenericStorage,
    pow: f32) -> (f32, f32)
{
    storage.step(&pow)
}

#[pyclass]
#[derive(Clone)]
pub struct EnSySimEnv {
    #[pyo3(get)]
    done: bool,
    current_step: usize, // ?
    main_cell: Option<cell::Cell>,
    slp_phh: Vec<f32>,
    slp_bsla: Vec<f32>,
    slp_bslc: Vec<f32>,
    hot_water_data: Vec<f32>,
    t: Vec<f32>,
    e_global: Vec<f32>,
    e_diffuse: Vec<f32>,
    e_direct: Vec<f32>,
    e_elevation: Vec<f32>,
    e_azimuth: Vec<f32>,
}

    
#[pymethods]
impl EnSySimEnv {

    #[new]
    pub fn new(slp_data: HashMap<&str, Vec<f32>>,
               hot_water_data: PyReadonlyArrayDyn<f32>,
               env_data: HashMap<&str, Vec<f32>>,
               sol_data: HashMap<&str, Vec<f32>>) -> Self {


        let hot_water_data = hot_water_data.to_vec().unwrap();

        let slp_phh = slp_data.get("PHH").unwrap();
        let slp_bsla = slp_data.get("BSLa").unwrap();
        let slp_bslc = slp_data.get("BSLc").unwrap();

        let t = env_data.get("T [degC]").unwrap();
        let e_global = env_data.get("Eg [W/m^2]").unwrap();
        let e_diffuse = env_data.get("E diffuse [W/m^2]").unwrap();
        let e_direct = env_data.get("E direct [W/m^2]").unwrap();
        let e_elevation = sol_data.get("elevation [degree]").unwrap();
        let e_azimuth = sol_data.get("azimuth [degree]").unwrap();
     
        let env = EnSySimEnv{
                  done: false,
                  current_step: 0,
                  main_cell: None,
                  slp_phh: slp_phh.to_vec(),
                  slp_bsla: slp_bsla.to_vec(),
                  slp_bslc: slp_bslc.to_vec(),
                  hot_water_data: hot_water_data,
                  t: t.to_vec(),
                  e_global: e_global.to_vec(),
                  e_diffuse: e_diffuse.to_vec(),
                  e_direct: e_direct.to_vec(),
                  e_elevation: e_elevation.to_vec(),
                  e_azimuth: e_azimuth.to_vec(),
        };
        env
    }

    pub fn add_cell(&mut self, main_cell: cell::Cell)
    {
        // only one thermal system per cell
        match &self.main_cell {
            None => self.main_cell = Some(main_cell),
            Some(_) => error!("cell already added")
        }
    }


    /// choose random starting point and initialize e. g. storages
    pub fn reset(&mut self)
    {
        self.current_step = rand::thread_rng().gen_range(0..35040);
    }

    /// step cell one time step
    pub fn step(&mut self)
    {
        // set data for actual step
        // SLP

        match &mut self.main_cell {
            None => error!("add cell first!"),
            Some(cell) => {
                let mut slp: [f32; 3] = [0.; 3];
                slp[0] = self.slp_phh[self.current_step];
                slp[1] = self.slp_bsla[self.current_step];
                slp[2] = self.slp_bslc[self.current_step];
        
               // Get Environment data and create object
               let mut amb = misc::ambient::AmbientParameters::new(0., 0., 0., 0., 0., 0.);
        
                // Environment
                amb.t_out = self.t[self.current_step];
                let idx_day = self.current_step.div_floor(& 96);
                let slice_day = &self.t[idx_day*96..idx_day*96+95];
                
                amb.t_mean_day = slice_day.iter().sum::<f32>() / slice_day.len() as f32;
                amb.irradiation_glob = self.e_global[self.current_step];
                amb.irradiation_diff = self.e_diffuse[self.current_step];
                amb.irradiation_dir = self.e_direct[self.current_step];
                amb.solar_elevation = self.e_elevation[self.current_step];
                amb.solar_azimuth = self.e_azimuth[self.current_step];
        
                // get the constant to a new memory place,
                //since cell can be changed due saving history
        
                let cell_t_out_n: f32 = cell.t_out_n;
        
                cell.step(&slp,
                          &self.hot_water_data[self.current_step],
                          &cell_t_out_n,
                          &mut amb);

                self.current_step += 1;
            },
        }
    }
}