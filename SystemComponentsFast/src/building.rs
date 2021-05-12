// external
use pyo3::prelude::*;
use log::error;

use crate::{agent, save_e, save_t};
use crate::components::{controller, pv};
use crate::misc::hist_memory;

use crate::thermal_systems::building::{heatpump_system, chp_system};

use crate::misc::ambient::AmbientParameters;


#[derive(Clone)]
enum HeatingSystem {
    ChpSystem(chp_system::BuildingChpSystem),
    HeatpumpSystem(heatpump_system::BuildingHeatpumpSystem),
}

impl HeatingSystem {
    /// Calculate heating system and get generated thermal power and
    /// generated (positive) or consumed (negative) electrical power
    ///
    /// # Arguments
    /// * heating_demand (&f32): Thermal power needed for
    ///                          heating the building [W]
    /// * hot_water_demand (&f32): Thermal power needed by agents for
    ///                            warm water [W]
    /// * t_out (&f32): Outside temperature [degC]
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    fn step(&mut self, heating_demand: &f32, hot_water_demand: &f32,
            t_out: &f32, t_heat_lim: &f32, t_out_mean: &f32) -> (f32, f32)
    {
        match self {
            HeatingSystem::ChpSystem(system) =>
                system.step(heating_demand,
                            hot_water_demand,
                            t_heat_lim, t_out_mean),
            HeatingSystem::HeatpumpSystem(system) =>
                system.step(heating_demand,
                            hot_water_demand, t_out,
                            t_heat_lim, t_out_mean),
            //_ => (0., 0.)
        }
    }
    /// Get last losses of specific heating system
    ///
    /// # Returns
    /// * f32: Losses of last time step [W]
    fn get_losses(&self) -> &f32
    {
        match self {
            HeatingSystem::ChpSystem(system) => system.get_losses(),
            HeatingSystem::HeatpumpSystem(system) => system.get_losses(),
            //_ => &0.
        }
    }
}


#[pyclass]
#[derive(Clone)]
pub struct Building {
    #[pyo3(get)]
    pub agents: Vec<agent::Agent>,
    #[pyo3(get)]
    n_max_agents: u32,
    #[pyo3(get)]
    n_agents: u32,
    #[pyo3(get)]
    a_living: f32,  // Buildings living space m^2
    areas_uv: Vec<[f32; 2]>,  // m^2; W / (K m^2)
    delta_u: f32,  // W / (K m^2)
    n_infiltration: f32,  // 1h
    n_ventilation: f32,  // 1h
    res_u_trans: f32,  // resulting heat transmission coefficient W/K
    cp_eff: f32,  // effective heat storage coefficient Wh/K
    g: f32,  // Solar factor of building windows 0 to 1
    temperature: f32,  // estimation of mean building temperature degC
    nominal_temperature: f32,  // temperature set-point of building degC
    // min. outside temperature, where no heating is needed
    heat_lim_temperature: f32,  // degC
    mean_outside_temperature: f32,  // degC
    #[pyo3(set, get)]
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
    heating_system: Option<HeatingSystem>,
    heat_building: fn(&mut Building, &f32, &f32, &f32) -> (f32, f32),
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
    /// * a_living (f32): Buildings living space [m^2]
    /// * areas_uv: (Vec<[f32; 2]>): All building areas [m^2]
    ///                              and corresponding
    ///                              U-Values [W/(m^2 K)]
    ///                              needed for norm heat load calculation
    /// * delta_u (f32): Offset for U-Value correction [W/(m^2 K)]
    ///                  (see calculateNormHeatLoad for details)
    /// * n_infiltration (f32): Air infiltration rate of building [1/h]
    /// * n_ventilation (f32): Air infiltration rate due ventilation [1/h]
    /// * cp_eff (f32): Effective heat storage coefficient of building [Wh/K]
    /// * g (f32): Solar factor of building windows 0 to 1 [-]
    /// * volume (f32): Inner building Volume [m^3]
    ///                 (This Value is used for calculation
    ///                 of air renewal losses)
    /// * is_at_dhn (bool): If true building is connected to the
    ///                     district heating network
    /// * t_out_n (f32): Normed outside temperature for
    ///                  region of building [°C]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    fn new(n_max_agents: u32, a_living:f32,
           areas_uv: Vec<[f32; 2]>, delta_u: f32,
           n_infiltration: f32, n_ventilation: f32, cp_eff: f32, g: f32,
           volume: f32, is_at_dhn: bool, t_out_n: f32, hist: usize) -> Self {
        // check parameter
        if n_max_agents <= 0 {
            panic!("Number of max. Agents must be greater than 0");
        }

        if a_living < 0. {
            panic!("Buildings living space must be greater than 0")
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

        if (g < 0.) | (g > 1.) {
            panic!("Solar factor must be between 0 and 1");
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
                            n_max_agents,
                            n_agents: 0,
                            agents: Vec::new(),
                            a_living,
                            areas_uv,
                            delta_u,
                            n_infiltration,
                            n_ventilation,
                            res_u_trans: 0.,
                            cp_eff,
                            g: g,
                            temperature: 20.,
                            nominal_temperature: 20.,
                            heat_lim_temperature: 15.,
                            mean_outside_temperature: 15.,
                            v: volume,
                            q_hln: 0.,
                            is_at_dhn,
                            is_self_supplied_t: !is_at_dhn,
                            controller: default_controller,
                            pv: None,
                            heating_system: None,
                            heat_building: Building::get_dhn_generation,
                            gen_e,
                            gen_t,
                            load_e,
                            load_t,
                            temperature_hist,
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
            error!("Number of max. Agents reached, \
                   no agent is added");
        }
    }

    fn add_pv(&mut self, pv: pv::PV) {
        match &self.pv {
            None => {self.pv = Some(pv);},
            Some(_building_pv) => error!("Building already has a \
                                         PV plant, nothing is added"),
        }
    }

    fn add_heatpump(&mut self,
                    heatpump_sytem: heatpump_system::BuildingHeatpumpSystem)
    {
        // building can have either chp or heatpump
        match &self.heating_system {
            // for now only one heatpump per building is allowed
            None => {self.heating_system =
                        Some(HeatingSystem::HeatpumpSystem(heatpump_sytem));
                     self.is_self_supplied_t = false;
                     self.heat_building = Building::get_hs_generation;
            },
            Some(_building_chp) => error!("Building already has a \
                                           heating system"),
        }
    }

    fn add_chp(&mut self,
               chp_system: chp_system::BuildingChpSystem) {
        // building can have either chp or heatpump
        match &self.heating_system {
            // for now only one heatpump per building is allowed
            None => {self.heating_system =
                        Some(HeatingSystem::ChpSystem(chp_system));
                     self.is_self_supplied_t = false;
                     self.heat_building = Building::get_hs_generation;
            },
            Some(_) => error!("Building already has a heating system"),
        }
    }

    /// Add PV with dimensioning of installed PV power
    /// by agents demand statistics
    /// and AmbientParameterss global irradiation history.
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
                                t_out_n: f32,
                                hist: usize)
    {
        self.add_heatpump(
            heatpump_system::BuildingHeatpumpSystem
                ::new(self.q_hln,
                      seas_perf_fac,
                      t_supply,
                      t_ref,
                      self.heat_lim_temperature,
                      t_out_n,
                      hist));
    }

    fn add_dimensioned_chp(&mut self, hist: usize)
    {
        self.add_chp(
            chp_system::BuildingChpSystem::new(self.q_hln,
                                               self.n_max_agents as f32,
                                               hist));
    }

    fn get_chp_system(&self) -> Option<chp_system::BuildingChpSystem>
    {
        match &self.heating_system {
            Some(HeatingSystem::ChpSystem(system)) => {
                Some(system.clone())
            },
            _ => None,
        }
    }

    fn get_hp_system(&self) -> Option<heatpump_system::BuildingHeatpumpSystem>
    {
        match &self.heating_system {
            Some(HeatingSystem::HeatpumpSystem(system)) => {
                Some(system.clone())
            },
            _ => None,
        }
    }

    fn has_heating_system(&self) -> PyResult<bool>
    {
        match &self.heating_system {
            Some(_) => Ok(true),
            None => Ok(false)
        }
    }

    fn replace_agent(&mut self, agent_pos: usize, agent: agent::Agent){
        if agent_pos > (self.n_agents - 1) as usize {
            error!("Agent position exceeds number of available Agents. \
                   Max. possiblie agent position is {}",
                   self.n_agents - 1);
        } else {
            self.agents[agent_pos] = agent;
        }
    }
}

impl Building {
    const TIME_STEP: f32 = 0.25;  // h
    const N: f32 = 1. * 24. / Building::TIME_STEP;
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
        // Update heating limit temperature
        self.update_t_heat_lim();
    }

    fn get_pv_generation(&mut self, eg: &f32) -> f32 {
        match &mut self.pv {
            None => 0.,
            Some(building_pv) => building_pv.step(eg)
        }
    }

    /// Function to calculate thermal generation of building,
    /// if it's at district heating network or if it's self supplied.
    ///
    /// Space heating demand is determined by internal control algorithm.
    ///
    /// # Arguments
    /// * sh_power_request (&f32): Thermal power requested for
    ///                            space heating [W]
    /// * thermal_load_hw (&f32): Hot water demand [W]
    /// * t_out (&f32): Outside temperature [degC]
    ///
    /// # Returns
    /// * (f32, f32): (electrical generation/load = 0., thermal generation)
    fn get_dhn_generation(&mut self, sh_power_request: &f32,
                          thermal_load_hw: &f32, _t_out: &f32) -> (f32, f32)
    {
            // Building is self-supplied
            (0., sh_power_request + thermal_load_hw)
    }

    /// Function to calculate thermal generation of buildings heating system.
    ///
    /// A positive electrical return means generation (e.g. chp)
    /// A negative electrical return mean consumption (e.g. heatpump)
    ///
    /// Space heating demand is determined by internal control algorithm.
    ///
    /// # Arguments
    /// * sh_power_request (&f32): Thermal power requested for
    ///                            space heating [W]
    /// * thermal_load_hw (&f32): Hot water demand [W]
    /// * t_out (&f32): Outside temperature [degC]
    ///
    /// # Returns
    /// * (f32, f32): (electrical generation/load, thermal generation)
    fn get_hs_generation(&mut self, sh_power_request: &f32,
                          thermal_load_hw: &f32, t_out: &f32) -> (f32, f32)
    {
        match &mut self.heating_system {
            None => (0., 0.),
            Some(heating_system) => {
                heating_system.step(&(sh_power_request -
                                    heating_system.get_losses()).max(0.),
                                    thermal_load_hw, t_out,
                                    &self.heat_lim_temperature,
                                    &self.mean_outside_temperature)
                },
            }
    }

    /// Calculate solar gains in W
    ///
    /// Building walls are east, south, west, north straight.
    /// Window area gets allocated uniformly (1/4th per direction)
    fn get_solar_gains(&self, amb: &AmbientParameters) -> f32 {
        let window_area = self.areas_uv[1][0];
        // south, west, north, east
        let irradiations = amb.specific_gains;

        let mut solar_gain = 0.;

        for view in irradiations.iter() {
            solar_gain += view * window_area / 4.;
        }
        solar_gain * self.g
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

    /// Calculate the min. heat temperature by an simple lin. regression model
    /// The model is based on data of "Energiedepesche 01/2007"
    ///
    ///     T(P) = 0.05 P + 10.34
    ///
    /// The resulting Temperature value is limited to the min / max values of
    /// the data (9.5 degC / 17 degC)
    fn update_t_heat_lim(&mut self) {
        self.heat_lim_temperature =
          (0.05 * self.q_hln / self.a_living + 10.34).min(17.).max(9.5);
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
                amb: &AmbientParameters) -> (f32, f32, f32, f32) {
        // init current step
        let mut electrical_load = 0.;
        let thermal_load_heat;  // space heating demand
        let mut thermal_load_hw = 0.;  // hot water demand
        let mut dhn_load = 0.;  // thermal load for cells dhn
        let mut electrical_generation = 0.;
        let mut internal_gains = 0.;  // internal gains for space heating
        self.update_mean_t_out(&amb.t_out);

        // calculate loads
        self.agents.iter().for_each(|agent: &agent::Agent| {
            let (sub_load_e, sub_load_t) = agent.step(slp_data, hw_profile);
            electrical_load += sub_load_e;
            thermal_load_hw += sub_load_t;
        });
        // Electric energy consumed in building will heat it up (DIN 4108-6)
        internal_gains += electrical_load;
        // solar irradiation through windows will heat building
        internal_gains += self.get_solar_gains(&amb);

        // PV
        electrical_generation += self.get_pv_generation(&amb.irradiation_glob);

        // Heating
        let sh_power_request = self.temperature_control(&internal_gains,
                                                        &amb.t_out);
        let (sub_e, thermal_generation) = (self.heat_building)
            (self, &sh_power_request, &thermal_load_hw, &amb.t_out);

        // electrical effect of heating systems must not be considered
        // for internal gains, since they are considered by the thermal part
        if sub_e < 0. {
            electrical_load -= sub_e;  // sub_e is negative -> minus means plus
        } else {
            electrical_generation += sub_e;
        }

        // add load for dhn
        if self.is_at_dhn {
            dhn_load = thermal_generation;
        }

        // Update building temperature and resulting thermal load
        // For space heating generation, the hot water generation must be
        // subtracted from complete thermal generation.
        thermal_load_heat = self.get_space_heating_demand(&(internal_gains +
                                                            thermal_generation -
                                                            thermal_load_hw),
                                                          &amb.t_out);


        // save data
        save_e!(self, electrical_generation, electrical_load);
        save_t!(self, thermal_generation + internal_gains,
                thermal_load_heat + thermal_load_hw);

        return (electrical_generation, electrical_load,
                0., dhn_load);
    }

    /// Simple bang-bang controller to keep building temperature at desired
    /// set point or heat building up. Cooling is not considered.
    ///
    /// # Arguments
    /// * internal_gains (&f32): Internal heat gains of building [W]
    /// * t_out (&f32): Outside temperature [degC]
    ///
    /// # Returns
    /// * f32: Requested Heating power [W]
    fn temperature_control(&mut self, internal_gains: &f32,
                           t_out: &f32) -> f32
    {
        let (heat_loss, heat_up);

        // thermal heat needed for heating up the building in one time step
        // or overhang of thermal energy (then heat_up is negative)
        heat_up = self.cp_eff * (self.nominal_temperature -
                                 self.temperature) / Building::TIME_STEP;

        if self.temperature < *t_out {
            heat_loss = 0.;
        } else {
            // predicted heat losses
            heat_loss = self.res_u_trans * (self.temperature - *t_out);
        }

        (heat_loss + heat_up - *internal_gains).max(0.)
    }

    /// Update mean outside temperature registered by building
    /// The mean is calculated as recursive value:
    ///     Tmean = (n-1)/n*Tmean_last + 1/n*T
    ///
    /// n is set to 24h / TimeStep
    ///
    /// # Arguments
    /// * t_out (&f32): Outside temperature [degC]
    fn update_mean_t_out(&mut self, t_out: &f32) {
        self.mean_outside_temperature =
          (Building::N - 1.) / (Building::N) * self.mean_outside_temperature +
          1. / Building::N * t_out;
    }
}