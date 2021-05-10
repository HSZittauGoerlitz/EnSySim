// external
use pyo3::prelude::*;
use log::{info};

use crate::boiler::Boiler;
use crate::chp::CHP;
use crate::generic_storage::GenericStorage;
use crate::hist_memory;


#[pyclass]
#[derive(Clone)]
pub struct TheresaSystem {
    #[pyo3(get)]
    chp: CHP,  // chp plant
    #[pyo3(get)]
    storage: GenericStorage,  // thermal storage for dhn
    #[pyo3(get)]
    boiler: Boiler,  // peak load boiler (electric)

    // Controller variables
    boiler_state: bool,
    chp_state: bool,

    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl TheresaSystem {
    #[new]
    pub fn new(hist: usize) -> Self {

        let p_max = 200e3;  // Max. available thermal power [W]
        let chp_proportion = 0.6;  // proportion of chp at p_max

        let chp = CHP::new(chp_proportion*p_max, hist);

        let storage = GenericStorage::new(73.6e3,
                                          0.98,
                                          0.98,
                                          0.,
                                          p_max,
                                          hist,);

        // boiler
        let boiler = Boiler::new((1. - chp_proportion)*p_max, hist);

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

        TheresaSystem {chp,
                       storage,
                       boiler,
                       boiler_state: false,
                       chp_state: false,
                       gen_e,
                       gen_t,
                       }
    }
}

impl TheresaSystem {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.3;
    const STORAGE_LEVEL_L: f32 = 0.2;
    const STORAGE_LEVEL_LL: f32 = 0.05;

    fn control(&mut self){
        let storage_state = self.storage.get_relative_charge();

        if storage_state <= TheresaSystem::STORAGE_LEVEL_LL {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= TheresaSystem::STORAGE_LEVEL_L) &
                !self.chp_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= TheresaSystem::STORAGE_LEVEL_H) &
                self.boiler_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= TheresaSystem::STORAGE_LEVEL_HH {
            self.chp_state = false;
            self.boiler_state = false;
        }
    }

    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * thermal_demand (&f32): Thermal power needed by dhn [W]
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, thermal_demand: &f32)
    -> (f32, f32)
    {
        self.control();

        let (pow_e, chp_t) = self.chp.step(&self.chp_state);
        let boiler_t = self.boiler.step(&self.boiler_state);

        let pow_t = chp_t + boiler_t;

        // call storage step -> check if all energy could be processed
        let (storage_diff, storage_loss) =
            self.storage.step(&(pow_t - thermal_demand));

        // save production data
        self.save_hist(&pow_e, &pow_t);

        // return supply data
        return (pow_e, thermal_demand + storage_diff);
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
}