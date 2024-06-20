// external
use pyo3::prelude::*;
use std::collections::HashMap;
use log::error;

use crate::{building, sep_bsl_agent, save_e, save_t};
use crate::components::pv;
use crate::components::solarthermal;
use crate::components::wind;
use crate::misc::{hist_memory};
use crate::misc::ambient::AmbientParameters;
use crate::misc::cell_manager::CellManager;
use crate::thermal_systems::cell::{chp_system_thermal,
                                   theresa_system,
                                   tms_system_thermal_electrical};


#[derive(Clone)]
enum ThermalSystem {
    ChpSystem(chp_system_thermal::CellChpSystemThermal),
    TheresaSystem(theresa_system::TheresaSystem),
    TMSSystem(tms_system_thermal_electrical::CellTmsSystemThermalElectrical),
}

impl ThermalSystem {
    /// Calculate thermal system and get generated thermal power and
    /// generated (positive) or consumed (negative) electrical power
    ///
    /// # Arguments
    /// * thermal_demand (&f32): Thermal power requested by dhn [W]
    /// * cell_state (&CellManager): All necessary cell informations
    /// * amb (&AmbientParameters): Current Ambient Measurements
    ///
    /// # Returns
    /// * (f32, f32, f32): Resulting electrical and thermal power
    ///                    and fuel used by system [W]
    fn step(&mut self,
            thermal_demand: &f32,
            electrical_balance: &f32,
            cell_state: &CellManager,
            amb: &AmbientParameters)
    -> (f32, f32, f32)
    {
        match self {
            ThermalSystem::ChpSystem(system)
                =>system.step(thermal_demand,
                              cell_state,
                              amb),
            ThermalSystem::TheresaSystem(system)
                => system.step(thermal_demand),
            ThermalSystem::TMSSystem(system)
                => system.step(thermal_demand,
                               electrical_balance,
                               cell_state,
                               amb),
            //_ => (0., 0., 0.)
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
    #[pyo3(get)]
    solarthermal: Option<solarthermal::Solarthermal>,
    #[pyo3(get)]
    wind: Option<wind::Wind>,
    thermal_system: Option<ThermalSystem>,
    state: CellManager,
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

        let (gen_e,
             gen_t,
             load_e,
             load_t);

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
              solarthermal: None,
              wind: None,
              thermal_system: None,
              state: CellManager::new(),
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

    fn add_chp_thermal(&mut self,
                       chp_system: chp_system_thermal::CellChpSystemThermal)
    {
        // only one thermal system per cell
        match &self.thermal_system {
            None => self.thermal_system =
                        Some(ThermalSystem::ChpSystem(chp_system)),
            Some(_) => error!("Cell already has thermal system")
        }
    }

    fn add_tms_thermal_electrical(&mut self,
                                  tms_system: tms_system_thermal_electrical::
                                  CellTmsSystemThermalElectrical)
    {
        // only one thermal system per cell
        match &self.thermal_system {
            None => self.thermal_system =
                        Some(ThermalSystem::TMSSystem(tms_system)),
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

    fn add_solarthermal(&mut self, solarthermal: solarthermal::Solarthermal) {
        match &self.solarthermal {
            None => {self.solarthermal = Some(solarthermal);},
            Some(_cell_solarthermal) => error!("Cell already has a \
                                     Solarthermal plant, nothing is added"),
        }
    }

    fn add_wind_turbine(&mut self, wind: wind::Wind) {
        match &self.wind {
            None => {self.wind = Some(wind);},
            Some(_cell_wind) => error!("Cell already has a \
                                        wind turbine, nothing is added")
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

    /// Calculate a max. expectable thermal demand in current cell.
    /// If this cell is supplying sub-cells, it's recommended to consider
    /// also their demand for the dimensioning of the thermal system. Hence,
    /// this function can include all sub-cells, by setting the
    /// appropriate flag. In more specific cases, the thermal demand must be
    /// determined directly by the python model.
    ///
    /// # Arguments
    /// * include_sub_cells (bool): If true, the thermal demand from sub-cells
    ///                             is added to the current cell demand
    ///
    /// # Returns
    /// f32: Max. expectable thermal demand of cell [W]
    fn get_thermal_demand(&self, include_sub_cells: bool) -> PyResult<f32>
    {
        let mut demand_t = 0.;

        if include_sub_cells {
            for sub_cell in self.sub_cells.iter() {
                demand_t += sub_cell.get_thermal_demand(include_sub_cells)
                                .unwrap();
            }
        }
        for building in self.buildings.iter() {
            if building.is_at_dhn {
                demand_t += building.q_hln();
                for agent in building.agents.iter() {
                    demand_t += agent.hw_demand();
                }
            }
        }

        // BSL Agents cannot be connected to dhn

        Ok(demand_t)
    }

    fn get_theresa_system(&self) -> Option<theresa_system::TheresaSystem>
    {
        match &self.thermal_system {
            Some(ThermalSystem::TheresaSystem(system)) => {
                Some(system.clone())
            },
            _ => None,
        }
    }

    fn get_thermal_chp_system(&self) -> Option<chp_system_thermal::
                                        CellChpSystemThermal>
    {
        match &self.thermal_system {
            Some(ThermalSystem::ChpSystem(system)) => {
                Some(system.clone())
            },
            _ => None,
        }
    }

    fn get_thermal_tms_system(&self) -> Option<tms_system_thermal_electrical::
                                        CellTmsSystemThermalElectrical>
    {
        match &self.thermal_system {
            Some(ThermalSystem::TMSSystem(system)) => {
                Some(system.clone())
            },
            _ => None,
        }
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

    /// Step cell from python
    ///
    /// # Arguments
    /// pe (f32): Electrical power [W]
    ///     - negative: Load
    ///     - positive: Generation
    /// pt (f32): Thermal power of dhn [W]
    ///     - negative: Load
    ///     - positive: Generation
    /// * slp_data (HashMap<&str, f32>): Standard load profile data for
    ///     - "PHH": phh agents
    ///     - "BSLa": agriculture business agents
    ///     - "BSLc": common business agents
    /// * hw_profile (f32): Actual hot water day profile factor [-]
    /// * env_data (HashMap<&str, f32>): All Environment/Weather data
    ///     needed for the simulation
    /// * sol_data (HashMap<&str, f32>): Elevation and azimut of sun
    ///
    /// # Returns
    /// * (f32, f32, f32, f32): Current electrical and thermal
    ///                         power consumption and generation [W]
    fn py_step(&mut self, pe: f32, pt: f32,
               slp_data: HashMap<&str, f32>, hw_profile: f32,
               env_data: HashMap<&str, f32>,
               sol_data: HashMap<&str, f32>)
    -> PyResult<(f32, f32, f32, f32)>
    {
        // Prepare data for cell step
        let slp: [f32; 3] = [
            *slp_data.get("PHH").unwrap(),
            *slp_data.get("BSLa").unwrap(),
            *slp_data.get("BSLc").unwrap()
        ];
        let mut amb = AmbientParameters::new(
            *env_data.get("E direct [W/m^2]").unwrap(),
            *env_data.get("E diffuse [W/m^2]").unwrap(),
            *sol_data.get("elevation [degree]").unwrap(),
            *sol_data.get("azimuth [degree]").unwrap(),
            *env_data.get("wind speed [m/s]").unwrap(),
            *env_data.get("T [degC]").unwrap(),
            *env_data.get("T mean [degC]").unwrap()
        );

        let t_out_n = self.t_out_n;

        let (mut gen_e, mut load_e, mut gen_t, mut load_t) =
            self.step(&slp, &hw_profile, &t_out_n, &mut amb);

        if pe > 0. {
            gen_e += pe;
        } else {
            load_e -= pe;
        }
        if pt > 0. {
            gen_t += pt;
        } else {
            load_t -= pt;
        }

        Ok((gen_e, load_e, gen_t, load_t))
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

    fn get_solarthermal_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.solarthermal {
            None => 0.,
            Some(cell_solarthermal) => {
                 cell_solarthermal.step(eg)
            },
        }
    }

    fn get_wind_generation(&mut self, ws: &f32) -> f32 {
        match &mut self.wind {
            None => 0.,
            Some(cell_wind) => {
                cell_wind.step(ws)
            }
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
                                                ) / h.sin();
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
    /// * t_out_n (&f32): Normed outside temperature for
    ///                   region of building [°C]
    /// * amb (&mut AmbientParameters): Current Ambient Measurements
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

        // calculate electrical generation systems
        electrical_generation += self.get_pv_generation(&amb.irradiation_glob);
        electrical_generation += self.get_wind_generation(&amb.wind_speed);

        // calculate thermal generation systems
        thermal_generation += self.get_solarthermal_generation(&amb.irradiation_glob);
        let (ts_e, ts_t_gen, ts_fuel);
        match &mut self.thermal_system {
            None =>
            {
                ts_e = 0.;
                ts_t_gen = 0.;
                ts_fuel = 0.;
            },
            Some(system) =>
            {
                let ts_e_t_f =
                    system.step(&((thermal_load -
                                    thermal_generation).max(0.)),
                                &(electrical_load - 
                                    electrical_generation),
                                &self.state, amb
                                );
                // unpack tuple, since unpacking without let is buggy
                ts_e = ts_e_t_f.0;
                ts_t_gen = ts_e_t_f.1;
                ts_fuel = ts_e_t_f.2;
                thermal_generation += ts_t_gen;
                // check if thermal system generated or
                // consumed electrical energy
                if ts_e > 0. {
                    electrical_generation += ts_e;
                } else {
                    electrical_load -= ts_e;  // ts_e is negative -> - is +
                }
            }
        }
        self.state.update(&electrical_generation, &electrical_load,
                          &thermal_generation, &thermal_load,
                          &ts_e, &ts_t_gen, &ts_fuel);
        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation, thermal_load);

        return (electrical_generation, electrical_load,
                thermal_generation, thermal_load);
    }
}