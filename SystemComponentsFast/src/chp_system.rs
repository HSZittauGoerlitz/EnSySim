// external
use pyo3::prelude::*;
use log::{debug};

use crate::helper::min_index;

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
        let pow_t = 0.8 * q_hln;
        let chp = CHP::new(pow_t, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C,
        let c_water = 1.162;  // (Wh) / (kg K)
        let rho_water = 983.2;  // kg / m^3
        // Available storage volumes in m^3
        let models: [f32;11] = [0.2, 0.3, 0.4, 0.5, 0.6, 0.75,
                                0.95, 1.5, 2., 3., 5.];
        let mut diffs: [f32;11] = [0.;11];
        let exact = pow_t * 50.0e-3; // kW * m^3/kW

        for (pos, model) in models.iter().enumerate() {
            diffs[pos] = (exact - model).abs();
        }

        let index = min_index(&diffs);

        let volume = models[index];
        let cap = volume * c_water * rho_water * 40.; // in Wh

        // dummy parameters for now
        let storage = GenericStorage::new(cap,
                                          0.95,
                                          0.95,
                                          0.05,
                                          q_hln,
                                          hist,);

        // hot water storage
        // Min. capacity according to DIN
        // 5820. Wh is the energy needed to fill standard bathtub
        let w_2tn = 5820. * n * ((1. + n.sqrt()) / n.sqrt());
        // Volume needed for this capacity
        // diff. between cold and hot water: 60. K
        let min_volume_hw = w_2tn / (60. * c_water * rho_water);

        // find hot water storage volume
        let mut volume_hw = *models.last().unwrap();
        for model in models.iter() {
            if min_volume_hw < *model {
                volume_hw = *model;
                break;
            }
        }

        // dummy parameters for now
        let cap_hw = volume_hw * c_water * rho_water * 60.; // in Wh
        let storage_hw = GenericStorage::new(cap_hw,
                                             0.95,
                                             0.95,
                                             0.05,
                                             q_hln,
                                             hist,);

        // boiler
        let pow_t = 0.2 * q_hln;
        let boiler = Boiler::new(pow_t, hist);

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
                                    gen_e: gen_e,
                                    gen_t: gen_t,
                                    };
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
    /// * thermal_load (&f32): thermal load of building this time step
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, thermal_load: &f32) -> (f32, f32) {
        // system satisfies heat demand from building
        // this is done by emptying storage
        // if state is true, system needs to actively produce heat
        // first chp is turned on and adds heat to storage,
        // boiler only turns on, if this is not enough
        // excess heat is destroyed
        // ToDo: add partial load to chp and boiler
        // ToDo: check if chp does not over supply system -> boiler
        let storage_state = self.storage.get_relative_charge();
        let storage_state_hw = self.storage_hw.get_relative_charge();
        debug!("storage state: {}", storage_state);

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
            self.chp_state = false;
            self.boiler_state = false;
        }

        // overwrite boiler state by hot water storage state
        // -> higher priority for boiler operation
        // -> Deactivation should occur in course of chp operation
        if !self.boiler_state &
           (storage_state_hw <= ChpSystem::STORAGE_LEVEL_4) {
               self.boiler_state = true;
        }

        let (pow_e, chp_t) = self.chp.step(&self.chp_state);
        let boiler_t = self.boiler.step(&self.boiler_state);

        let pow_t = chp_t + boiler_t;
        let storage_t = pow_t - thermal_load;

        // call storage step -> check if all energy could be processed
        let storage_diff = self.storage.step(&storage_t);

        // save production data
        self.save_hist(&pow_e, &pow_t);

        // return supply data
        return (pow_e, thermal_load + storage_diff);
    }
}