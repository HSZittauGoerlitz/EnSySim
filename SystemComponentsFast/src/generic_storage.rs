// external
use pyo3::prelude::*;
use rand::prelude::*;
use log::{debug};

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct GenericStorage {
    #[pyo3(get)]
    cap: f32,  // capacity of storage [Wh]
    charge: f32,  // charging state of storage [Wh] -> get_charge()
    charging_efficiency: f32,  // 0..1
    discharging_efficiency: f32,  // 0..1
    self_discharge: f32,  // 0..1 [1/h] ToDo: function of charge (only thermal)
    // ToDo: cycle dacay (only electrical)
    pow_max: f32,  // maximum power flow in or out of storage [W]
    #[pyo3(get)]
    charge_hist: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl GenericStorage {
    ///  Create storage with specific capacity
    ///  This simplest model accounts only for the energy balance,
    ///  no mass flows/temperatures are considered.
    ///  Loading state is randomly initialized.
    ///
    /// # Arguments
    /// * cap (f32): installed capacity [Wh]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(cap: f32, 
               charging_efficiency: f32,
               discharging_efficiency: f32,
               self_discharge:f32,
               pow_max: f32,
               hist: usize) -> Self {

        let cap = cap;

        // random loading state
        let mut rng = rand::thread_rng();
        let charge = rng.gen::<f32>() * cap;

        // history
        let charge_hist;

        if hist > 0 {
            charge_hist = Some(hist_memory::HistMemory::new(hist));
        } else {
            charge_hist = None;
        }

        let generic_storage = GenericStorage {
                              cap: cap,
                              charge: charge,
                              charging_efficiency: charging_efficiency,
                              discharging_efficiency: discharging_efficiency,
                              self_discharge: self_discharge,
                              pow_max: pow_max,
                              charge_hist: charge_hist,
                                              };
        generic_storage
    }
}

/// thermal storage
impl GenericStorage {

    const TIME_STEP: f32 = 0.25;

    pub fn get_relative_charge(& self) -> f32 {
        return self.charge / self.cap
    }

    fn charge_storage(& mut self, pow: &f32) -> f32 {
        // check for a) maximum power flow and b) free storage capacity
        let mut diff = pow - self.pow_max;

        if pow * self.charging_efficiency <= (self.cap - self.charge) / GenericStorage::TIME_STEP {
            if diff > 0. {
                self.charge += self.pow_max * GenericStorage::TIME_STEP * self.charging_efficiency;
            }
            else {
                self.charge += pow * GenericStorage::TIME_STEP * self.charging_efficiency;
                diff = 0.
            }
        }
        else {
            diff = pow * self.charging_efficiency - (self.cap - self.charge) / GenericStorage::TIME_STEP;

            self.charge = self.cap;
        }
        return diff  // didn´t fit into storage, positive
    }

    fn discharge_storage(& mut self, pow: &f32) -> f32 {
        // check for a) maximum power flow and b) available storage content
        let mut diff = self.pow_max - pow;

        if pow / self.discharging_efficiency <= self.charge / GenericStorage::TIME_STEP {
            if diff < 0. {
                self.charge -= self.pow_max * GenericStorage::TIME_STEP
                               / self.discharging_efficiency;
            }
            else {
                self.charge -= pow * GenericStorage::TIME_STEP 
                               / self.discharging_efficiency;
                diff = 0.
            }
        }
        else {
            diff = self.charge / GenericStorage::TIME_STEP - pow / self.discharging_efficiency;
            self.charge = 0.;
        }
        return diff  // couldn´t be supplied, negative
    }

    fn save_hist(&mut self) {
        match &mut self.charge_hist {
            None => {},
            Some(charge_hist) => {
                charge_hist.save(self.charge)
            }
        }
    }

    /// Calculate new charging state
    ///
    /// # Arguments
    /// * power input of surrounding system, may be positive or negative
    ///
    /// # Returns
    /// * f32: Not received or delivered power [W], difference between 
    ///        requested and handled power
    pub fn step(&mut self, pow: &f32) -> f32 {

        let mut diff = 0.;

        if *pow >= 0. {
            diff = self.charge_storage(&pow);
        }
        else if *pow < 0. {
            diff = self.discharge_storage(&(-1. * pow));
        }

        self.charge = self.charge - self.charge * self.self_discharge * GenericStorage::TIME_STEP;

        // save data
        self.save_hist();

        debug!("pow: {} ,diff:{}, charge: {}", pow, diff, self.charge);

        return diff;
    }
}