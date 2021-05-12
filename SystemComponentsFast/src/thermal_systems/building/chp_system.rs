// external
use pyo3::prelude::*;
use rand::Rng;
use log::{info};

use crate::misc::helper::{find_heating_system_storage,
                          find_heat_storage_loss_parameter,
                          find_hot_water_system_storage};

use crate::components::boiler::Boiler;
use crate::components::chp::CHP;
use crate::components::generic_storage::GenericStorage;
use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct BuildingChpSystem {
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
    control_mode: u8,  // 0: Winter, 1: Intermediate, 2: Summer
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
impl BuildingChpSystem {
    /// Create CHP system with thermal storage and boiler
    /// The technical design is based on norm heating load.
    ///
    /// The hot water system is designed according to DIN 4708.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building [W]
    /// * n (f32): Characteristic number for buildings hot water demand
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, n: f32, hist: usize) -> Self {
        if q_hln < 0. {
            panic!("Norm heating load of building must be a positive number")
        }
        if n < 0. {
            panic!("Characteristic number for buildings hot water demand \
                    must be positive")
        }

        let mut rng = rand::thread_rng();
        let f_chp: f32 = rng.gen_range(0.3..=0.6);
        // chp:
        let pow_t_chp = f_chp * q_hln;
        let chp = CHP::new(pow_t_chp, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C,
        let (cap, volume) = find_heating_system_storage(&pow_t_chp, &40.);
        let self_loss = find_heat_storage_loss_parameter(&volume, &cap);

        // dummy parameters for now
        let storage = GenericStorage::new(cap,
                                          0.95,
                                          0.95,
                                          self_loss,
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
                                             0.01,
                                             cap_hw / 0.5,  // cap_hw/...h -> W
                                             hist,);

        // boiler
        let pow_t_boiler = (1. - f_chp) * q_hln;
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

        info!("
               designed chp system with following specifications:
               chp nominal power: {:.2}kW
               heating storage capacity: {:.2}kWh
               hot water storage capcaity: {:.2}kWh
               boiler nominal power: {:.2}kW",
               pow_t_chp/1000., cap/1000., cap_hw/1000., pow_t_boiler/1000.);

        BuildingChpSystem {chp,
                   storage,
                   storage_hw,
                   boiler,
                   boiler_state: false,
                   chp_state: false,
                   control_mode: 1,
                   t_heat_lim_h: 0.5,
                   last_losses: 0.,
                   gen_e,
                   gen_t,
                   }
    }
}

/// CHP plant
impl BuildingChpSystem {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.3;
    const STORAGE_LEVEL_L: f32 = 0.2;
    const STORAGE_LEVEL_LL: f32 = 0.05;

    fn control(&mut self){
        match self.control_mode {
            0 => self.winter_mode(),
            1 => self.intermediate_mode(),
            2 => self.summer_mode(),
            _ => panic!("Unknown control mode {} of chp system",
                        self.control_mode),
        }
    }

    pub fn get_losses(&self) -> &f32 {
        &self.last_losses
    }

    fn intermediate_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();
        let storage_state_hw = self.storage_hw.get_relative_charge();

        if self.boiler_state {self.boiler_state = false;}
        if (storage_state <= BuildingChpSystem::STORAGE_LEVEL_LL) |
           (storage_state_hw <= BuildingChpSystem::STORAGE_LEVEL_LL)
        {
            self.chp_state = true;
        }
        else if (storage_state >= BuildingChpSystem::STORAGE_LEVEL_H) &
                (storage_state_hw >= BuildingChpSystem::STORAGE_LEVEL_HH)
        {
            self.chp_state = false;
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
        self.control();

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

    fn summer_mode(&mut self) {
        let storage_state_hw = self.storage_hw.get_relative_charge();

        if self.boiler_state {self.boiler_state = false;}
        if storage_state_hw <= BuildingChpSystem::STORAGE_LEVEL_LL {
            self.chp_state = true;
        }
        else if storage_state_hw >= BuildingChpSystem::STORAGE_LEVEL_HH {
            self.chp_state = false;
        }
    }

    /// Change Control mode
    ///
    /// 0: Winter
    /// 1: Intermediate
    /// 2: Summer
    ///
    /// # Arguments
    /// * t_heat_lim (&f32): min. outside temperature of building,
    ///                      where no heating is needed  [degC]
    /// * t_out_mean (&f32): Mean outside temperature of buildings region in
    ///                      last hours [degC]
    fn update_control_mode(&mut self, t_heat_lim: &f32, t_out_mean: &f32)
    {
        // Get actual control mode
        match self.control_mode {
            0 => {
                if *t_out_mean > (*t_heat_lim - 0.8*self.t_heat_lim_h) {
                    self.control_mode = 1;
                }
            },
            1 => {
                if *t_out_mean > (*t_heat_lim + 1.2*self.t_heat_lim_h) {
                    self.control_mode = 2;
                }
                else if *t_out_mean < (*t_heat_lim - 1.2*self.t_heat_lim_h) {
                    self.control_mode = 0;
                }
            },
            2 => {
                if *t_out_mean < (*t_heat_lim + 0.8*self.t_heat_lim_h) {
                    self.control_mode = 1;
                }
            },
            _ => panic!("Unknown control mode {} of chp system",
                        self.control_mode),
        }
    }

    fn winter_mode(&mut self) {
        let storage_state = self.storage.get_relative_charge();
        let storage_state_hw = self.storage_hw.get_relative_charge();

        if storage_state <= BuildingChpSystem::STORAGE_LEVEL_LL {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= BuildingChpSystem::STORAGE_LEVEL_L) &
                !self.chp_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= BuildingChpSystem::STORAGE_LEVEL_H) &
                self.boiler_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= BuildingChpSystem::STORAGE_LEVEL_HH {
            if storage_state_hw >= BuildingChpSystem::STORAGE_LEVEL_HH {
                self.chp_state = false;
            }
            self.boiler_state = false;
        }

        if storage_state_hw <= BuildingChpSystem::STORAGE_LEVEL_LL {
            self.chp_state = true;
        }
    }
}
