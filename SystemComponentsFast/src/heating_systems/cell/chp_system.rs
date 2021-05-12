// external
use pyo3::prelude::*;

use crate::boiler::Boiler;
use crate::chp::CHP;
use crate::generic_storage::GenericStorage;
use crate::hist_memory;


#[pyclass]
#[derive(Clone)]
pub struct CellChpSystem {
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
impl CellChpSystem {
    /// Create thermal supply system for a cell,
    /// based on chp, boiler and thermal storage.
    ///
    /// # Arguments
    /// * p_th (f32): Thermal power of complete system [W]
    /// * chp_prop (f32): Proportion of chp on p_th
    /// * storage_cap (f32): Capacity of storage [Wh]
    /// * storage_self_loss (f32): Self loss storage [1/h]
    /// * storage_charge_eff (f32): Storage charging efficiency [-]
    /// * storage_discharge_eff (f32): Storage discharging efficiency [-]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(p_th: f32, chp_prop: f32,
               storage_cap: f32, storage_self_loss: f32,
               storage_charge_eff: f32, storage_discharge_eff: f32,
               hist: usize) -> Self
    {
        let chp = CHP::new(chp_prop*p_th, hist);

        let storage = GenericStorage::new(storage_cap,
                                          storage_charge_eff,
                                          storage_discharge_eff,
                                          storage_self_loss,
                                          p_th,
                                          hist);

        // boiler
        let boiler = Boiler::new((1. - chp_prop)*p_th, hist);

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

        CellChpSystem {chp,
                       storage,
                       boiler,
                       boiler_state: false,
                       chp_state: false,
                       gen_e,
                       gen_t,
                       }
    }
}

impl CellChpSystem {
    // Control Parameter
    const STORAGE_LEVEL_HH: f32 = 0.95;
    const STORAGE_LEVEL_H: f32 = 0.3;
    const STORAGE_LEVEL_L: f32 = 0.2;
    const STORAGE_LEVEL_LL: f32 = 0.05;

    fn control(&mut self){
        let storage_state = self.storage.get_relative_charge();

        if storage_state <= CellChpSystem::STORAGE_LEVEL_LL {
            self.boiler_state = true;
            self.chp_state = true;
        }
        else if (storage_state <= CellChpSystem::STORAGE_LEVEL_L) &
                !self.chp_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if (storage_state >= CellChpSystem::STORAGE_LEVEL_H) &
                self.boiler_state {
            self.boiler_state = false;
            self.chp_state = true;
        }
        else if storage_state >= CellChpSystem::STORAGE_LEVEL_HH {
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
        let (storage_diff, _) =
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