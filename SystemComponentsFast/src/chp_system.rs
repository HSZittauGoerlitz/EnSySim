// external
use pyo3::prelude::*;
use log::{info};

use crate::helper::{find_heating_system_storage,
                    find_hot_water_system_storage};

use crate::boiler::Boiler;
use crate::chp::CHP;
use crate::generic_storage::GenericStorage;
use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ChpSystem {
    #[pyo3(get)]
    chp: CHP,  // chp plant
    #[pyo3(get)]
    storage: GenericStorage,  // thermal storage
    #[pyo3(get)]
    storage_hw: GenericStorage,  // storage of hot water system
    #[pyo3(get)]
    boiler: Boiler,  // peak load boiler

    // Controller variables
    boiler_state: bool,
    chp_state: bool,
    summer_mode: bool,  // control mode: True -> Summer, False -> Winter
    // Hysteresis for control mode in relation to buildings lim. Temp.
    t_heat_lim_h: f32,  // degC
    // save storage losses, to consider in temperature control
    last_losses: f32,  // W
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl ChpSystem {
    /// Create CHP system with thermal storage and boiler
    /// The technical design is based on norm heating load.
    ///
    /// The hot water system is designed according to DIN 4708.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building
    /// * n (f32): Characteristic number for buildings hot water demand
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, n: f32, hist: usize) -> Self {

        // chp:
        let pow_t_chp = 0.4 * q_hln;
        let chp = CHP::new(pow_t_chp, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C,
        let cap = find_heating_system_storage(&pow_t_chp, &40.);

        // dummy parameters for now
        let storage = GenericStorage::new(cap,
                                          0.95,
                                          0.95,
                                          0.05,
                                          q_hln,
                                          hist,);

        // hot water storage
        // diff. between cold and hot water: 60. K
        let cap_hw = find_hot_water_system_storage(&n, &60.);
        // dummy parameters for now
        // TODO: Which power is adequate?
        let storage_hw = GenericStorage::new(cap_hw,
                                             0.95,
                                             0.95,
                                             0.05,
                                             cap_hw / 0.5,  // cap_hw/...h -> W
                                             hist,);

        // boiler
        let pow_t_boiler = 0.6 * q_hln;
        let boiler = Boiler::new(pow_t_boiler, hist);

        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        }
        else {
            gen_e = None;
            gen_t = None;
        }

        let chp_system = ChpSystem {chp: chp,
                                    storage: storage,
                                    storage_hw: storage_hw,
                                    boiler: boiler,
                                    boiler_state: false,
                                    chp_state: false,
                                    summer_mode: false,
                                    t_heat_lim_h: 1.5,
                                    last_losses: 0.,
                                    gen_e: gen_e,
                                    gen_t: gen_t,
                                    };

        info!("
               designed chp system with following specifications:
               chp nominal power: {:.2}kW
               heating storage capacity: {:.2}kWh
               hot water storage capcaity: {:.2}kWh
               boiler nominal power: {:.2}kW",
               pow_t_chp/1000., cap/1000., cap_hw/1000., pow_t_boiler/1000.);

        chp_system
    }
}

/// CHP plant
impl ChpSystem {
    // Control Parameter
    const STORAGE_LEVEL_1: f32 = 0.95;
    const STORAGE_LEVEL_2: f32 = 0.6;
    const STORAGE_LEVEL_3: f32 = 0.3;
    const STORAGE_LEVEL_4: f32 = 0.2;

    pub fn get_losses(&self) -> &f32 {
        &self.last_losses
    }

    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*pow_e)
            },
        }
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }

    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * heating_demand (&f32): Thermal power needed for
    ///                          heating the building [W]
    /// * hot_water_demand (&f32): Thermal power needed by agents for
    ///                            warm water [W]
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, heating_demand: &f32, hot_water_demand: &f32,
                t_heat_lim: &f32, t_out_mean: &f32)
    -> (f32, f32)
    {
        // system satisfies heat demand from building
        // this is done by emptying storage
        // if state is true, system needs to actively produce heat
        // first chp is turned on and adds heat to storage,
        // boiler only turns on, if this is not enough
        // excess heat is destroyed
        // ToDo: add partial load to chp and boiler
        // ToDo: check if chp does not over supply system -> boiler

        self.update_control_mode(t_heat_lim, t_out_mean);
        if self.summer_mode {
            self.summer_mode();
        } else {
            self.winter_mode();
        }

        let (pow_e, chp_t) = self.chp.step(&self.chp_state);
        let boiler_t = self.boiler.step(&self.boiler_state);

        // call hot water storage with CHP power
        //-> differences will be used by heating system
        let storage_hw_t = chp_t - hot_water_demand;
        let (storage_hw_diff, storage_hw_loss) =
          self.storage_hw.step(&storage_hw_t);

        let pow_t = storage_hw_diff + boiler_t;
        let storage_t = pow_t - heating_demand;

        // call storage step -> check if all energy could be processed
        let (storage_diff, storage_loss) = self.storage.step(&storage_t);

        self.last_losses = storage_hw_loss + storage_loss;

        // save production data
        self.save_hist(&pow_e, &pow_t);

        // return supply data
        return (pow_e, *heating_demand + *hot_water_demand + storage_diff +
                       storage_hw_loss + storage_loss);
    }

    fn summer_mode(&mut self) {
        let storage_state_hw = self.storage_hw.get_relative_charge();

        self.boiler_state = false;
        if storage_state_hw <= ChpSystem::STORAGE_LEVEL_4 {
            self.chp_state = true;
        }
        else if storage_state_hw >= ChpSystem::STORAGE_LEVEL_1 {
            self.chp_state = false;
        }
    }
    /// # Arguments
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    fn update_control_mode(&mut self, t_heat_lim: &f32, t_out_mean: &f32)
    {
        if self.summer_mode {
            if *t_out_mean < (*t_heat_lim - self.t_heat_lim_h) {
                self.summer_mode = false;
            }
        } else {
            if *t_out_mean > (*t_heat_lim + self.t_heat_lim_h) {
                self.summer_mode = true;
            }
        }
    }

    fn winter_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();
        let storage_state_hw = self.storage_hw.get_relative_charge();

        if storage_state <= ChpSystem::STORAGE_LEVEL_4 {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= ChpSystem::STORAGE_LEVEL_3) &
                !self.chp_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= ChpSystem::STORAGE_LEVEL_2) &
                self.boiler_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= ChpSystem::STORAGE_LEVEL_1 {
            if storage_state_hw >= ChpSystem::STORAGE_LEVEL_1 {
                self.chp_state = false;
            }
            self.boiler_state = false;
        }

        if storage_state_hw <= ChpSystem::STORAGE_LEVEL_4 {
            self.chp_state = true;
        }
    }
}