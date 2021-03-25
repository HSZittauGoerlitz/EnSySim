// external
use pyo3::prelude::*;
use log::{debug};

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
    ///  Create CHP system with thermal storage and boiler
    ///  The technical design is based on norm heating load.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, hist: usize) -> Self {

        // chp:
        let pow_t = 0.8 * q_hln;
        let chp = CHP::new(pow_t, hist);

        // thermal storage:
        // 75l~kg per kW thermal generation, 40K difference -> 60°C,
        //c_water = 4.184 KJ(kg*K)
        let models: [f32;11] = [200., 300., 400., 500., 600., 750.,
                                950., 1500., 2000., 3000., 5000.];
        let mut diffs: [f32;11] = [0.;11];
        let exact = pow_t * 50.0; // kW * l/kW

        for (pos, model) in models.iter().enumerate() {
            diffs[pos] = (exact - model).abs();
        }

        let index = min_index(&diffs);
        // ToDo: bring to helper.rs file
        fn min_index(array: &[f32]) -> usize {
            let mut i = 0;

            for (j, &value) in array.iter().enumerate() {
                if value < array[i] {
                    i = j;
                }
            }

            i
        }
        let volume = models[index];
        let cap = volume * 4.184*1000. * 40. / 3600.; // in Wh

        // dummy parameters for now
        let storage = GenericStorage::new(cap,
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

        let time_step = 0.25; // ToDo: time step fixed

        // system satisfies heat demand from building
        // this is done by emptying storage
        // if state is true, system needs to actively produce heat
        // first chp is turned on and adds heat to storage,
        // boiler only turns on, if this is not enough
        // excess heat is destroyed
        // ToDo: add partial load to chp and boiler
        // ToDo: check if chp does not over supply system -> boiler
        let storage_state = self.storage.get_relative_charge();
        debug!("storage state: {}", storage_state);

        if storage_state <= ChpSystem::STORAGE_LEVEL_4 {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= ChpSystem::STORAGE_LEVEL_3) &
                (self.chp_state == false) {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= ChpSystem::STORAGE_LEVEL_2) &
                (self.boiler_state == true) {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= ChpSystem::STORAGE_LEVEL_1 {
            self.chp_state = false;
            self.boiler_state = false;
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