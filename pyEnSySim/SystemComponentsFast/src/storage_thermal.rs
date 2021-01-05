// external
use pyo3::prelude::*;
use rand::Rng;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ThermalStorage {
    state: i8,  // charging/do nothing/uncharging (-1/0/1) switch
    cap: f32,  // capacity of thermal storage [J]
    charge: f32,  // charging state of storage [J]
    temp_charge: f32, // variable for storing charge requests
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
        let charge = rng.gen_range(0, 1) * cap;

        let temp_charge;
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
                     temp_charge: temp_charge,
                     charge_t: charge_t,
                    };
        thermal_storage
    }
}

/// thermal storage
impl ThermalStorage {
    fn save_hist_c(&mut self, charge: &f32) {
        match &mut self.gen_t {
            None => {},
            Some(charge_t) => {
                charge_t.save(*charge)
            }
        }
    }

    /// Charge and discharge storeage during time step
    pub fn charge(&mut self, pow_t: &f32) {
        // charge storage with thermal power, 
        // charging state update happens in step()
        let self.temp_charge += pow_t*time_step; //ToDo: time step
    }

    /// Calculate thermal power and new charging state
    ///
    /// # Arguments
    /// * state (&i8): Current state of storage (charging/off/discharging)
    ///
    /// # Returns
    /// * f32: Resulting thermal power [W]
    pub fn step(&mut self, thermal_load: f32) -> f32 {

        // delivered to building
        let pow_t = thermal_load;
        // calculate balance reset temps
        let balance = self.temp_charge/time_step - self.pow_t; //ToDo: time step
        let self.temp_charge = 0;

        // update charge
        let self.charge = self.charge + balance*time_step; //ToDo: time step
        // ToDo!: handling full and empty cases

        // save data
        self.save_hist_c(&self.charge);

        return pow_t;
    }
}