// external
use pyo3::prelude::*;
use log::error;

use crate::{building, pv, sep_bsl_agent,
            hist_memory, save_e, save_t};
use crate::heating_systems::cell::{chp_system, theresa_system};

use crate::ambient::AmbientParameters;


#[derive(Clone)]
enum ThermalSystem {
    ChpSystem(chp_system::CellChpSystem),
    TheresaSystem(theresa_system::TheresaSystem),
}

impl ThermalSystem {
    /// Calculate thermal system and get generated thermal power and
    /// generated (positive) or consumed (negative) electrical power
    ///
    /// # Arguments
    /// * thermal_demand (&f32): Thermal power requested by dhn [W]
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    fn step(&mut self, thermal_demand: &f32) -> (f32, f32)
    {
        match self {
            ThermalSystem::ChpSystem(system) => system.step(thermal_demand),
            ThermalSystem::TheresaSystem(system) =>
                system.step(thermal_demand),
            //_ => (0., 0.)
        }
    }
}


#[pyclass]
#[derive(Clone)]
pub struct Cell {
    #[pyo3(get)]
    sub_cells: Vec<Cell>,
    #[pyo3(get)]
    buildings: Vec<building::Building>,
    #[pyo3(get)]
    sep_bsl_agents: Vec<sep_bsl_agent::SepBSLagent>,
    #[pyo3(get)]
    n_cells: u32,
    #[pyo3(get)]
    n_buildings: u32,
    #[pyo3(get)]
    n_sep_bsl_agents: u32,
    #[pyo3(get)]
    eg: f32,
    #[pyo3(get)]
    pub t_out_n: f32,
    #[pyo3(get)]
    pv: Option<pv::PV>,
    thermal_system: Option<ThermalSystem>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Cell {
    ///  Create cell to simulate a energy grid segment
    ///
    /// # Arguments
    /// * eg (f32): Mean annual global irradiation
    ///               for simulated region [kWh/m^2]
    /// * t_out_n (f32): Normed outside temperature for
    ///                  specific region in °C
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(eg: f32, t_out_n: f32, hist: usize) -> Self {
        if eg < 0. {
            panic!("Mean annual global irradiation is a negative number")
        }

        let (gen_e, gen_t, load_e, load_t);

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
            load_e = Some(hist_memory::HistMemory::new(hist));
            load_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
            load_e = None;
            load_t = None;
        }

        Cell {sub_cells: Vec::new(),
              n_cells: 0,
              buildings: Vec::new(),
              n_buildings: 0,
              sep_bsl_agents: Vec::new(),
              n_sep_bsl_agents: 0,
              eg: eg,
              t_out_n: t_out_n,
              pv: None,
              thermal_system: None,
              gen_e: gen_e,
              gen_t: gen_t,
              load_e: load_e,
              load_t: load_t,
              }
    }

    fn add_building(&mut self, building: building::Building) {
        self.buildings.push(building);
        self.n_buildings += 1;
    }

    fn add_cell(&mut self, cell:Cell) {
        self.sub_cells.push(cell);
        self.n_cells += 1;
    }

    fn add_chp(&mut self,
               chp_system: chp_system::CellChpSystem)
    {
        // only one thermal system per cell
        match &self.thermal_system {
            None => self.thermal_system =
                        Some(ThermalSystem::ChpSystem(chp_system)),
            Some(_) => error!("Cell already has thermal system")
        }
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_cell_pv) => error!("Cell already has a \
                                     PV plant, nothing is added"),
        }
    }

    fn add_sep_bsl_agent(&mut self,
                         sep_bsl_agent: sep_bsl_agent::SepBSLagent) {
        self.sep_bsl_agents.push(sep_bsl_agent);
        self.n_sep_bsl_agents += 1;
    }

    fn add_theresa(&mut self,
                   theresa_system: theresa_system::TheresaSystem)
    {
        // only one thermal system per cell
        match &self.thermal_system {
            None => self.thermal_system =
                        Some(ThermalSystem::TheresaSystem(theresa_system)),
            Some(_) => error!("Cell already has thermal system")
        }
    }

    /// # Returns
    /// PyResult<f32>: Mean yearly electrical cell demand [Wh]
    fn get_electrical_demand(&self) -> PyResult<f32>
    {
        // get the sum of coc's in cell
        let mut coc = 0.;

        for sub_cell in self.sub_cells.iter() {
            coc += sub_cell.get_electrical_demand().unwrap();
        }
        for building in self.buildings.iter() {
            for agent in building.agents.iter() {
                coc += agent.coc();
            }
        }
        for agent in self.sep_bsl_agents.iter() {
            coc += agent.coc();
        }

        Ok(coc*1e6)  // coc is mean yearly demand per 1000 kWh -> * 1e3 * 1e3
    }

    fn replace_building(&mut self, building_pos: usize,
                        building: building::Building)
    {
        if building_pos > (self.n_buildings - 1) as usize {
            error!("Building position exceeds number of available buildings. \
                   Max. possiblie building position is {}",
                   self.n_buildings - 1);
        } else {
            self.buildings[building_pos] = building;
        }
    }

    fn update_building(&mut self, building_idx: usize,
                       building: building::Building)
    {
        self.buildings[building_idx] = building;
    }
}

impl Cell {
    fn get_pv_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.pv {
            None => 0.,
            Some(cell_pv) => {
                 cell_pv.step(eg)
            },
        }
    }

    /// Calculate area specific solar irradiation for windows facing
    /// south, west, north and east
    fn get_specific_solar_gains(&mut self,  amb: &mut AmbientParameters) {
        // first calculate direct part
        // south, west, north, east
        let mut irradiations = [0., 0., 0., 0.];
        let orientations: [f32; 4] = [0., 90., 180., 270.];

        let i_b: f32 = amb.irradiation_dir.to_radians();
        let h: f32 = amb.solar_elevation.to_radians();
        let tilt: f32 = std::f32::consts::FRAC_PI_2;
        let gamma: f32 = amb.solar_azimuth.to_radians();

        if h > 0. {
            for (idx, orientation) in orientations.iter().enumerate() {
                // Difference between window orientation and sun azimuth
                let delta = (*orientation).to_radians() - gamma;
                if (delta > -std::f32::consts::FRAC_PI_2) &
                   (delta < std::f32::consts::FRAC_PI_2) {
                    irradiations[idx] += i_b * (h.sin()*tilt.cos() +
                                                h.cos()*delta.cos()*tilt.sin()
                                                );
                   }
            }
        }

        // now diffuse part
        let i_d: f32 = amb.irradiation_diff;

        for idx in 0..irradiations.len() {
            irradiations[idx] += i_d * (1. + tilt.cos()) / 2.;
        }

        amb.specific_gains = irradiations;
    }



    /// Calculate and return current power consumption and generation
    /// This is the amount of power which can't be supplied by the cell itself.
    /// Hence this power is communicated, to be supplied by other cells.
    ///
    /// The total cell power balance can be found in the cell history.
    ///
    /// # Arguments
    /// * slp_data (&[f32; 3]): Standard load Profile of all agent types
    /// * hw_profile (&f32): Actual hot water day profile factor [-]
    /// * t_out (&f32): Current (daily mean) outside temperature [°C]
    /// * t_out_n (&f32): Normed outside temperature for
    ///                   region of building [°C]
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * (f32, f32, f32, f32): Current electrical and thermal
    ///                         power consumption and generation [W]
    pub fn step(&mut self, slp_data: &[f32; 3], hw_profile: &f32,
                t_out_n: &f32, amb: &mut AmbientParameters)
                -> (f32, f32, f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let mut thermal_load = 0.;
        let mut electrical_generation = 0.;
        let mut thermal_generation = 0.;

        // calculate sub cells
        self.sub_cells.iter_mut().for_each(|sc: &mut Cell| {
            let (sub_gen_e, sub_load_e, sub_gen_t, sub_load_t) =
                sc.step(slp_data, hw_profile,
                        t_out_n, amb);
            electrical_generation += sub_gen_e;
            thermal_generation += sub_gen_t;
            electrical_load += sub_load_e;
            thermal_load += sub_load_t;
        });

        // calculate buildings
        self.get_specific_solar_gains(amb);
        self.buildings.iter_mut().for_each(|b: &mut building::Building| {
            let (sub_gen_e, sub_load_e, sub_gen_t, sub_load_t) =
                b.step(slp_data, hw_profile, &amb);
            electrical_generation += sub_gen_e;
            thermal_generation += sub_gen_t;
            electrical_load += sub_load_e;
            thermal_load += sub_load_t;
        });

        // calculate separate BSL agents
        self.sep_bsl_agents.iter_mut().
            for_each(|sbsl: &mut sep_bsl_agent::SepBSLagent| {
                let (sub_gen_e, sub_load_e) =
                    sbsl.step(slp_data, &amb.irradiation_glob);
                electrical_generation += sub_gen_e;
                electrical_load += sub_load_e;
        });


        // calculate generation systems
        electrical_generation += self.get_pv_generation(&amb.irradiation_glob);
        match &mut self.thermal_system {
            None => (),
            Some(system) =>
                {
                    let (ts_e, ts_t_gen) = system.step(&thermal_load);
                    thermal_generation += ts_t_gen;
                    // check if thermal system generated or consumed electrical energy
                    if ts_e > 0. {
                        electrical_generation += ts_e;
                    } else {
                        electrical_load -= ts_e;  // ts_e is negative -> - is +
                    }
                }
        }
        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation, thermal_load);

        return (electrical_generation, electrical_load,
                thermal_generation, thermal_load);
    }
}