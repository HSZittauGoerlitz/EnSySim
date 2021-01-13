// external
use pyo3::prelude::*;
use rand::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ThermalStorage {
    state: i8,  // charging/do nothing/uncharging (-1/0/1) switch
    cap: f32,  // capacity of thermal storage [J]
    pub charge: f32,  // charging state of storage [J], ToDo: Get/Set?
    #[pyo3(get)]
    charge_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl ThermalStorage {
    ///  Create thermal storage with specific capacity
    ///
    /// # Arguments
    /// * cap (f32): installed capacity [J]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(cap: f32, hist: usize) -> Self {

        // storage:
        let cap = cap;
        let state = 0;

        let mut rng = rand::thread_rng();
        let mut charge = rng.gen::<f32>() * cap;

        let charge_t;

        // history
        if hist > 0 {
            charge_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            charge_t = None;
        }

        let thermal_storage = ThermalStorage {state: state,
                     cap: cap,
                     charge: charge,
                     charge_t: charge_t,
                    };
        thermal_storage
    }
}

/// thermal storage
impl ThermalStorage {
    fn save_hist_c(&mut self, charge: f32) {
        match &mut self.charge_t {
            None => {},
            Some(charge_t) => {
                charge_t.save(charge)
            }
        }
    }

    /// Calculate thermal power and new charging state
    ///
    /// # Arguments
    /// * thermal_load (&f32): load of supplied building
    ///
    /// # Returns
    /// * f32: Resulting thermal power [W]
    pub fn step(&mut self, thermal_load: &f32) -> f32 {

        let time_step = 0.25; // ToDo: time step fixed

        // delivered to building
        let pow_t = *thermal_load;

        self.charge -= pow_t*time_step;

        // save data
        self.save_hist_c(self.charge);

        return pow_t;
    }
}