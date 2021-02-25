// external
use pyo3::prelude::*;
use rand::prelude::*;
use log::{debug};

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ThermalStorage {
    cap: f32,  // capacity of thermal storage [J]
    charge: f32,  // charging state of storage [J] -> get_charge()
    #[pyo3(get)]
    charge_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl ThermalStorage {
    ///  Create thermal storage with specific capacity
    ///  This simplest model accounts only for the energy balance,
    ///  no mass flows/temperatures are considered.
    ///  Loading state is randomly initialized.
    ///
    /// # Arguments
    /// * cap (f32): installed capacity [J]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(cap: f32, hist: usize) -> Self {

        let cap = cap;

        // random loading state
        let mut rng = rand::thread_rng();
        let charge = rng.gen::<f32>() * cap;

        // history
        let charge_t;

        if hist > 0 {
            charge_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            charge_t = None;
        }

        let thermal_storage = ThermalStorage {cap: cap,
                     charge: charge,
                     charge_t: charge_t,
                    };
        thermal_storage
    }
}

/// thermal storage
impl ThermalStorage {
    pub fn get_charge(& self) -> f32 {
        return self.charge
    }

    fn save_hist_c(&mut self) {
        match &mut self.charge_t {
            None => {},
            Some(charge_t) => {
                charge_t.save(self.charge)
            }
        }
    }

    /// Calculate thermal power and new charging state
    ///
    /// # Arguments
    /// * thermal_generation (&f32): generation of chp system
    /// * thermal_load (&f32): load of supplied building
    ///
    /// # Returns
    /// * f32: Resulting thermal power [W]
    pub fn step(&mut self, thermal_generation: &f32, thermal_load: &f32) -> f32 {

        let time_step = 0.25; // ToDo: time step fixed

        // delivered to building
        let pow_t = *thermal_load;

        self.charge += *thermal_generation * time_step;
        self.charge -= pow_t * time_step;

        // get rid of excess heat
        if self.charge > self.cap {
            self.charge = self.cap;
        }
        // handle empty case
        if self.charge < 0. {
            debug!("storage is empty and could not supply enough heat!");
            self.charge = 0.;
        }
        
        // save data
        self.save_hist_c();

        return pow_t;
    }
}