// external
use pyo3::prelude::*;
use log::{debug, info, warn};

use crate::{agent, controller, pv, chp_system, hist_memory, save_e, save_t};

#[pyclass]
#[derive(Clone)]
pub struct Building {
    #[pyo3(get)]
    agents: Vec<agent::Agent>,
    #[pyo3(get)]
    n_max_agents: u32,
    #[pyo3(get)]
    n_agents: u32,
    areas_uv: Vec<[f32; 2]>,  // m2; W / (K m^)
    delta_u: f32,  // W / (K m^)
    n_infiltration: f32,  // 1h
    n_ventilation: f32,  // 1h
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
    chp: Option<chp_system::CHP_System>,
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    load_t: Option<hist_memory::HistMemory>,
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
    ///                             and corresponding
    ///                             U-Values [W/(m^2 K)]
    ///                             needed for norm heat load calculation
    /// * delta_u (f32): Offset for U-Value correction [W/(m^2 K)]
    ///                  (see calculateNormHeatLoad for details)
    /// * n_infiltration (f32): Air infiltration rate of building [^/h]
    /// * n_ventilation (f32): Air infiltration rate due ventilation [^/h]
    /// * v (f2): Inner building Volume [m^3]
    ///           (This Value is used for calculation
    ///            of air renewal losses)
    /// * is_at_dhn (bool): If true building is connected to the
    ///                     district heating network
    /// * t_out_n (f32): Normed outside temperature for
    ///                  region of building [°C]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    fn new(n_max_agents: u32, areas_uv: Vec<[f32; 2]>, delta_u: f32,
           n_infiltration: f32, n_ventilation: f32, volume: f32,
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

        let defaultController = controller::Controller::new();

        // Create object
        let mut building = Building {
            n_max_agents: n_max_agents,
            n_agents: 0,
            agents: Vec::new(),
            areas_uv: areas_uv,
            delta_u: delta_u,
            n_infiltration: n_infiltration,
            n_ventilation: n_ventilation,
            v: volume,
            q_hln: 0.,
            is_at_dhn: is_at_dhn,
            is_self_supplied_t: !is_at_dhn,
            controller: defaultController,
            pv: None,
            chp: None,
            gen_e: gen_e,
            gen_t: gen_t,
            load_e: load_e,
            load_t: load_t,
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
            print!("WARNING: Number of max. Agents reached,
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

    fn add_chp(&mut self, chp: chp_system::CHP_System) {
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

    fn add_dimensioned_chp(&mut self, hist: usize) {
        self.add_chp(chp_system::CHP_System::new(self.q_hln,
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
    /// # Arguments
    ///     t_out_n (f32): Normed outside temperature for
    ///                    region of building [°C]
    fn add_norm_heating_load(&mut self, t_out_n: &f32) {
        // Temperature Difference
        let d_t = 20. - t_out_n;
        // Transmission losses
        let mut phi_t = 0.;
        for a_uv in self.areas_uv.iter() {
            phi_t += a_uv[0] * (a_uv[1] + self.delta_u);
        }
        phi_t *= d_t;
        // Air renewal losses
        let phi_a = self.v * (self.n_infiltration + self.n_ventilation) *
                    0.3378 * d_t;

        self.q_hln = phi_t + phi_a;
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
                building_chp.step(&self.controller.get_chp_state(),
                                  &thermal_load)
            },
        }
    }

    /// Calculate space heating demand in W
    ///
    /// The space heating demand is calculated in relation to outside
    /// temperature and a building specific heating load.
    /// Based on a linear regression model the mean daily heating power is
    /// calculated. The space heating energy demand is determined by
    /// multiplicating this power with 24h.
    ///
    /// # Arguments
    /// * t_out (f32): Current (daily mean) outside temperature [°C]
    /// * t_out_n (f32): Normed outside temperature for
    ///                   region of building [°C]
    ///
    /// # Returns
    /// * f32: Space heating demand [W]
    fn get_space_heating_demand(&self, t_out: &f32, t_out_n: &f32) -> f32 {

        if *t_out < 15. {
            return self.q_hln * (t_out_n-t_out) / (15.-t_out_n) + self.q_hln;
        }
        else {
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
    /// * hw_profile (&f32): Actual hot water profile value [W]
    /// * t_out (&f32): Current (daily mean) outside temperature [°C]
    /// * t_out_n (&f32): Normed outside temperature for
    ///                   region of building [°C]
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * (f32, f32, f32, f32): Current electrical and thermal
    ///                         power consumption and generation [W]
    pub fn step(&mut self, slp_data: &[f32; 3], hw_profile: &f32,
                t_out: &f32, t_out_n: &f32, eg: &f32) -> (f32, f32, f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let mut thermal_load = 0.;
        let mut electrical_generation = 0.;
        let mut thermal_generation = 0.;

        // calculate loads
        self.agents.iter().for_each(|agent: &agent::Agent| {
            let (sub_load_e, sub_load_t) = agent.step(slp_data, hw_profile);
            electrical_load += sub_load_e;
            thermal_load += sub_load_t;
        });
        thermal_load += self.get_space_heating_demand(t_out, t_out_n);

        // calculate generation
        // chp
        let(sub_gen_e, sub_gen_t) = self.get_chp_generation(&thermal_load);
        electrical_generation += sub_gen_e;
        thermal_generation += sub_gen_t;
        // pv
        electrical_generation += self.get_pv_generation(eg);

        if self.is_self_supplied_t {
            // Building is self-supplied
            thermal_generation = thermal_load;
        }
        // TODO : Storage, Controller
        self.controller.step();

        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation, thermal_load);

        return (electrical_generation, electrical_load,
                thermal_generation, thermal_load);
    }
}