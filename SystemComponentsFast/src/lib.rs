// external
use std::collections::HashMap;
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use numpy::PyReadonlyArrayDyn;
// local
// Environment
mod ambient;
// Entities
#[macro_use]
mod agent;
mod building;
mod cell;
// Components
mod boiler;
mod chp;
mod controller;
mod generic_storage;
mod heating_systems;
mod heatpump;
mod pv;
mod sep_bsl_agent;
mod theresa_system;
// Misc
mod helper;
mod hist_memory;


#[pymodule]
fn SystemComponentsFast(_py: Python<'_>, m: &PyModule) -> PyResult<()> {

    pyo3_log::init();

    m.add_class::<agent::Agent>()?;
    m.add_class::<building::Building>()?;
    m.add_class::<cell::Cell>()?;
    m.add_class::<sep_bsl_agent::SepBSLagent>()?;
    m.add_class::<pv::PV>()?;
    m.add_class::<heating_systems::building
                  ::heatpump_system::BuildingHeatpumpSystem>()?;
    m.add_class::<heating_systems::building
                  ::chp_system::BuildingChpSystem>()?;
    m.add_class::<generic_storage::GenericStorage>()?;
    m.add_class::<theresa_system::TheresaSystem>()?;
    m.add_function(wrap_pyfunction!(simulate, m)?).unwrap();
    m.add_function(wrap_pyfunction!(test_generic_storage, m)?).unwrap();
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
    let mut amb = ambient::AmbientParameters::new(0., 0., 0., 0., 0.);
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
pub fn test_generic_storage(storage: &mut generic_storage::GenericStorage,
                            pow: f32) -> (f32, f32)
{
    storage.step(&pow)
}
