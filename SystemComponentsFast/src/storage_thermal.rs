// external
use pyo3::prelude::*;
use rand::prelude::*;
use log::{debug};

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ThermalStorage {
    #[pyo3(get)]
    cap: f32,  // capacity of thermal storage [Wh]
    charge: f32,  // charging state of storage [Wh] -> get_charge()
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
    /// * cap (f32): installed capacity [Wh]
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
    const TIME_STEP: f32 = 0.25; // [h] ToDo: Variable time steps

    /// Charge storage with given power
    ///
    /// # Arguments
    /// * charge_power (&f32): Power used for charging during time step [W]
    ///
    /// # Returns
    /// * f32: Power used for charging [W]
    fn charge_storage(&mut self, charge_power: &f32) -> f32 {
        // calculate new charge state
        self.charge += *charge_power * ThermalStorage::TIME_STEP;

        // check if all of given power could be used
        if self.charge > self.cap {
            let spillover = self.charge - self.cap;
            self.charge = self.cap;

            return *charge_power - spillover / ThermalStorage::TIME_STEP;
        }

        return *charge_power;
    }

    /// Discharge storage with given power
    ///
    /// # Arguments
    /// * discharge_power (&f32): Power requested during time step [W]
    ///
    /// # Returns
    /// * f32: Power provided by storage [W]
    fn discharge_storage(&mut self, discharge_power: &f32) -> f32 {
        // DISCHARGE POWER IS NEGATIVE
        // calculate new charge state
        self.charge += *discharge_power * ThermalStorage::TIME_STEP;

        // check if all of requested power could be delivered
        if self.charge < 0. {
            let deficit = -self.charge;
            self.charge = 0.;

            return *discharge_power + deficit / ThermalStorage::TIME_STEP;
        }

        return *discharge_power;
    }

    pub fn get_charge(& self) -> f32 {
        self.charge
    }

    pub fn get_relative_charge(& self) -> f32 {
        self.charge / self.cap
    }


    fn save_hist(&mut self) {
        match &mut self.charge_t {
            None => {},
            Some(charge_t) => {
                charge_t.save(self.charge)
            }
        }
    }

    /// Calculate chargin / dischargin of storage depending of given power
    ///  -> If given power is negative: discharge
    ///  -> If given power is positive: charge
    ///
    /// # Arguments
    /// * power (&f32): Charge / Discharge Powert for current time step [W]
    ///
    /// # Returns
    /// * f32: Power used for charging / discharging [W]
    pub fn step(&mut self, power: &f32) -> f32 {
        let mut pow_t: f32 = 0.;

        if *power > 0. {
            pow_t = self.charge_storage(power);
        } else if *power < 0. {
            pow_t = self.discharge_storage(power);
        }

        // save data
        self.save_hist();

        return pow_t;
    }
}