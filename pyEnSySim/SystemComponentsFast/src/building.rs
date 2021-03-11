// external
use pyo3::prelude::*;
use log::{warn};


use crate::{agent, controller, pv, heatpump_system, chp_system, hist_memory,
            save_e, save_t};

#[pyclass]
#[derive(Clone)]
pub struct Building {
    #[pyo3(get)]
    agents: Vec<agent::Agent>,
    #[pyo3(get)]
    n_max_agents: u32,
    #[pyo3(get)]
    n_agents: u32,
    areas_uv: Vec<[f32; 2]>,  // m^2; W / (K m^2)
    delta_u: f32,  // W / (K m^2)
    n_infiltration: f32,  // 1h
    n_ventilation: f32,  // 1h
    res_u_trans: f32,  // resulting heat transmission coefficient W/K
    cp_eff: f32,  // effective heat storage coefficient Wh/K
    temperature: f32, // estimation of mean building temperature degC
    #[pyo3(get)]
    is_at_dhn: bool,
    #[pyo3(get)]
    is_self_supplied_t: bool,
    v: f32,  // m3
    #[pyo3(get)]
    q_hln: f32,  // W
    #[pyo3(get)]
    controller: controller::Controller,
    #[pyo3(get)]
    pv: Option<pv::PV>,
    #[pyo3(get)]
    heatpump: Option<heatpump_system::HeatpumpSystem>,
    #[pyo3(get)]
    chp: Option<chp_system::ChpSystem>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    temperature_hist: Option<hist_memory::HistMemory>,
}

/// Class simulate buildings energy demand
#[pymethods]
impl Building {
    /// Create building
    ///
    /// # Arguments
    /// * nMaxAgents (u32): Number of max. possible agents
    ///                     living in this building
    /// * areas_uv: (Vec<[f32; 2]>): All building areas [m^2]
    ///                              and corresponding
    ///                              U-Values [W/(m^2 K)]
    ///                              needed for norm heat load calculation
    /// * delta_u (f32): Offset for U-Value correction [W/(m^2 K)]
    ///                  (see calculateNormHeatLoad for details)
    /// * n_infiltration (f32): Air infiltration rate of building [1/h]
    /// * n_ventilation (f32): Air infiltration rate due ventilation [1/h]
    /// * cp_eff (f32): Effective heat storage coefficient of building [Wh/K]
    /// * volume (f32): Inner building Volume [m^3]
    ///                 (This Value is used for calculation
    ///                 of air renewal losses)
    /// * is_at_dhn (bool): If true building is connected to the
    ///                     district heating network
    /// * t_out_n (f32): Normed outside temperature for
    ///                  region of building [°C]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    fn new(n_max_agents: u32, areas_uv: Vec<[f32; 2]>, delta_u: f32,
           n_infiltration: f32, n_ventilation: f32, cp_eff: f32, volume: f32,
           is_at_dhn: bool, t_out_n: f32, hist: usize) -> Self {
        // check parameter
        if n_max_agents <= 0 {
            panic!("Number of max. Agents must be greater than 0");
        }

        for a_uv in areas_uv.iter() {
            if a_uv[0] < 0. {
                panic!("Area is smaller than 0");
            }
            if a_uv[1] < 0. {
                panic!("U-Value is smaller than 0");
            }
        }
        if delta_u <= 0. {
            panic!("U-Value offset must not be negative");
        }
        if (n_infiltration < 0.) | (n_ventilation < 0.) {
            panic!("Infiltration rate must not be negative");
        }
        if volume < 0. {
            panic!("Building volume must not be negative");
        }

        let (gen_e, gen_t, load_e, load_t, temperature_hist);

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
            load_e = Some(hist_memory::HistMemory::new(hist));
            load_t = Some(hist_memory::HistMemory::new(hist));
            temperature_hist = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
            gen_t = None;
            load_e = None;
            load_t = None;
            temperature_hist = None;
        }

        let default_controller = controller::Controller::new();

        // Create object
        let mut building = Building {
            n_max_agents: n_max_agents,
            n_agents: 0,
            agents: Vec::new(),
            areas_uv: areas_uv,
            delta_u: delta_u,
            n_infiltration: n_infiltration,
            n_ventilation: n_ventilation,
            res_u_trans: 0.,
            cp_eff: cp_eff,
            temperature:20.,
            v: volume,
            q_hln: 0.,
            is_at_dhn: is_at_dhn,
            is_self_supplied_t: !is_at_dhn,
            controller: default_controller,
            pv: None,
            heatpump: None,
            chp: None,
            gen_e: gen_e,
            gen_t: gen_t,
            load_e: load_e,
            load_t: load_t,
            temperature_hist: temperature_hist,
        };
        building.add_norm_heating_load(&t_out_n);
        // all other possible components are empty
        // self.PV = None
        building
    }

    fn add_agent(&mut self, agent: agent::Agent) {
        if self.n_agents + 1 <= self.n_max_agents {
            self.agents.push(agent);
            self.n_agents += 1;
        }
        else {
            warn!("Number of max. Agents reached,
                   no agent is added");
        }
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_building_pv) => warn!("Building already has a
                                         PV plant, nothing is added"),
        }
    }

    fn add_heatpump(&mut self, heatpump: heatpump_system::HeatpumpSystem) {
        self.is_self_supplied_t = false;
        // building can have either chp or heatpump
        match &self.chp {
            // for now only one heatpump per building is allowed
            None => {match &self.heatpump {
                    None => {self.heatpump = Some(heatpump);},
                    Some(_building_heatpump) => warn!("Building already has a
                                                heatpump, nothing is added"),
                };
            },
            Some(_building_chp) => warn!("Building already has a chp,
                                        heatpump is not added"),
        }
    }

    fn add_chp(&mut self, chp: chp_system::ChpSystem) {
        self.is_self_supplied_t = false;
        match &self.chp {
            None => {self.chp = Some(chp);},
            Some(_building_chp) => warn!("Building already has a
                                          CHP plant, nothing is added"),
        }
    }

    /// Add PV with dimensioning of installed PV power
    /// by agents demand statistics
    /// and environments global irradiation history.
    ///
    /// # Arguments
    /// * Eg (f32): Mean annual global irradiation
    ///             for simulated region [kWh/m^2]
    /// * hist (usize): Size of history memory for pv plant (0 for no memory)
    fn add_dimensioned_pv(&mut self, eg: f32, hist: usize) {
        let mut sum_coc = 0.;
        let mut sum_apv_demand = 0.;
        let mut n_agents = 0;
        for idx in 0..self.agents.len() {
            sum_coc += self.agents[idx].coc();
            sum_apv_demand += self.agents[idx].demand_apv();
            n_agents += 1;
        }

        if n_agents == 0 {
            sum_apv_demand = 0.;
        } else {
            sum_apv_demand /= n_agents as f32;
        }

        self.add_pv(pv::PV::new(eg, sum_coc,
                                sum_apv_demand,
                                hist)
                    );
    }

    fn add_dimensioned_heatpump(&mut self,
                                seas_perf_fac: f32,
                                t_supply: f32,
                                t_ref: Vec<f32>,
                                hist: usize) {
        self.add_heatpump(heatpump_system::HeatpumpSystem::new(self.q_hln,
                                                               seas_perf_fac,
                                                               t_supply,
                                                               t_ref,
                                                               hist)
                         );
    }

    fn add_dimensioned_chp(&mut self, hist: usize) {
        self.add_chp(chp_system::ChpSystem::new(self.q_hln,
                                                 hist)
                     );
    }
}

impl Building {
    /// Calculate normed heating load Q_HLN of a building [W]
    ///
    /// The calculation is done in reference to the simplified method
    /// of DIN EN 12831-1:2017-09
    /// Modifications / Simplifications:
    ///     - Consideration of the whole building:
    ///         o normed room temperature is set to 20°C
    ///         o temperature matching coefficient is set to 1
    ///     - Normed air heat losses include infiltration losses
    ///
    /// The DIN Formulas are also use to determine the resulting
    /// heat transmission coefficient of the building.
    ///
    /// # Arguments
    ///     t_out_n (f32): Normed outside temperature for
    ///                    region of building [°C]
    fn add_norm_heating_load(&mut self, t_out_n: &f32) {
        // Calculate resulting transmission coefficient
        // Losses of Walls, Windows, Doors, Bridges, Floor / Roof
        for a_uv in self.areas_uv.iter() {
            self.res_u_trans += a_uv[0] * (a_uv[1] + self.delta_u);
        }
        // Air renewal losses
        self.res_u_trans += self.v * 0.3378 *
                            (self.n_infiltration + self.n_ventilation);
        // Calculate normed heating load
        self.q_hln = self.res_u_trans * (20. - t_out_n);
    }

    fn get_pv_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.pv {
            None => 0.,
            Some(building_pv) => {
                building_pv.step(eg)
            },
        }
    }

    fn get_chp_generation(&mut self, thermal_load: &f32) -> (f32, f32) {
        match &mut self.chp {
            None => (0., 0.),
            Some(building_chp) => {
                building_chp.step(&self.controller.chp_state,
                                  &thermal_load)
            },
        }
    }

    fn get_heatpump_generation(&mut self, thermal_load: &f32, t_out: &f32) -> (f32, f32) {
        match &mut self.heatpump {
            None => (0., 0.),
            Some(building_heatpump) => {
                building_heatpump.step(&self.controller.heatpump_state,
                                  &thermal_load,
                                  &t_out)
            },
        }
    }

    /// Calculate space heating demand in W
    ///
    /// At first the building temperature is calculated by the following DGL:
    ///
    ///     cp_eff*dT/dt = Q_in - u_eff*(T-T_out)
    ///
    /// The space heating demand is a function of the building temperature
    ///
    ///     Q_out = u_eff(T-T_out)
    ///
    /// # Arguments
    /// * q_in (&f32): Current thermal power delivered from heating system [W]
    /// * t_out (&f32): Current (daily mean) outside temperature [°C]
    ///
    /// # Returns
    /// * f32: Space heating demand [W]
    fn get_space_heating_demand(&mut self, q_in: &f32, t_out: &f32) -> f32 {
        // TODO: variable step size
        let quot_c_dt = self.cp_eff / 0.25;  // step size 0.25h

        self.temperature = 1. / (quot_c_dt + self.res_u_trans) *
                           (q_in + self.res_u_trans * t_out +
                            quot_c_dt * self.temperature);

        // save temperature history if available
        match &mut self.temperature_hist {
            None => {},
            Some(temperature_hist) => {
                temperature_hist.save(self.temperature)
            },
        }

        let demand = self.res_u_trans * (self.temperature - t_out);

        // Cooling is not considered here
        if demand > 0. {
            return demand;
        } else {
            return 0.;
        }
    }

    pub fn q_hln(&self) -> &f32 {
        &self.q_hln
    }


    /// Calculate and return current power consumption and generation
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
                t_out: &f32, eg: &f32) -> (f32, f32, f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let mut thermal_load_heat;  // space heating demand
        let mut thermal_load_hw = 0.;  // hot water demand
        let mut thermal_load;  // complete thermal demand
        let mut dhn_load = 0.;  // thermal load for cells dhn
        let mut electrical_generation = 0.;
        let mut thermal_generation = 0.;


        // calculate loads
        self.agents.iter().for_each(|agent: &agent::Agent| {
            let (sub_load_e, sub_load_t) = agent.step(slp_data, hw_profile);
            electrical_load += sub_load_e;
            thermal_load_hw += sub_load_t;
        });
        // predict heat losses by temperature of last time step
        thermal_load_heat = self.res_u_trans * (self.temperature - t_out);

        // only consider thermal load for heating
        if thermal_load_heat > 0. {
            thermal_load = thermal_load_hw + thermal_load_heat;
        } else {
            thermal_load = thermal_load_hw;
        }

        // calculate generation
        // chp
        let(sub_gen_e, sub_gen_t) =
            self.get_chp_generation(&thermal_load);
        electrical_generation += sub_gen_e;
        thermal_generation += sub_gen_t;
        // pv
        electrical_generation += self.get_pv_generation(eg);
        // heatpumps
        let(sub_load_e, sub_gen_t) =
            self.get_heatpump_generation(&thermal_load, &t_out);
        electrical_load += sub_load_e;
        thermal_generation += sub_gen_t;

        if self.is_self_supplied_t || self.is_at_dhn {
            // Building is self-supplied
            if self.temperature > 20. {
                thermal_generation = thermal_load_hw;
            } else {
                thermal_generation = thermal_load;
            }
        }

        // add load for dhn
        if self.is_at_dhn {
            dhn_load = thermal_generation;
        }

        // Update building temperature and resulting thermal load
        // For space heating generation, the hot water generation must be
        // subtracted from complete thermal generation.
        thermal_load_heat = self.get_space_heating_demand(&(thermal_generation -
                                                            thermal_load_hw),
                                                          &t_out);
        // Update complete thermal demand by correct space heating demand
        thermal_load = thermal_load_heat + thermal_load_hw;

        // TODO : Storage, Controller
        self.controller.step();

        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation, thermal_load);

        return (electrical_generation, electrical_load,
                0., dhn_load);
    }
}