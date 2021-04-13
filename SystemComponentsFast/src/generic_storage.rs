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
    #[pyo3(get)]
    charging_efficiency: f32,  // 0..1
    #[pyo3(get)]
    discharging_efficiency: f32,  // 0..1
    #[pyo3(get)]
    self_discharge: f32,  // 0..1 [1/h] ToDo: function of charge (only thermal)
    // ToDo: cycle dacay (only electrical)
    #[pyo3(get)]
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

    const TIME_STEP: f32 = 0.25;  // h

    pub fn get_relative_charge(& self) -> f32 {
        return self.charge / self.cap
    }

    /// Charge storage with given power
    ///
    /// # Arguments
    /// * charge_power (&f32): Power used for charging during time step [W]
    ///
    /// # Returns
    /// * f32: Power used for charging [W]
    fn charge_storage(& mut self, charge_power: &f32) -> f32 {
        // check for a) maximum power flow and b) free storage capacity
        let mut diff = *charge_power - self.pow_max;
        let resulting_charge_power;

        if diff > 0. {
            resulting_charge_power = self.pow_max;
        } else {
            resulting_charge_power = *charge_power;
            diff = 0.;
        }

        self.charge +=  resulting_charge_power * self.charging_efficiency *
                        GenericStorage::TIME_STEP;

        if self.charge > self.cap {
            diff += (self.charge - self.cap) / GenericStorage::TIME_STEP;
            self.charge = self.cap;
        }

        return diff  // didn´t fit into storage, positive
    }

    /// Discharge storage with given power
    ///
    /// Discharge Power is negative!
    ///
    /// # Arguments
    /// * discharge_power (&f32): Power requested during time step [W]
    ///
    /// # Returns
    /// * f32: Power provided by storage [W]
    fn discharge_storage(&mut self, discharge_power: &f32) -> f32 {
        // check for a) maximum power flow and b) available storage content
        let mut diff = *discharge_power + self.pow_max;
        let resulting_discharge_power;

        if diff < 0. {
            resulting_discharge_power = -self.pow_max;
        } else {
            resulting_discharge_power = *discharge_power;
            diff = 0.;
        }

        self.charge += resulting_discharge_power *
                       self.discharging_efficiency *
                       GenericStorage::TIME_STEP;

        if  self.charge < 0. {
            diff += self.charge / GenericStorage::TIME_STEP;
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

        let diff;

        if *pow > 0. {
            diff = self.charge_storage(pow);
        }
        else if *pow < 0. {
            diff = self.discharge_storage(pow);
        } else {
            diff = 0.;
        }

        self.charge = self.charge - self.charge * self.self_discharge *
                                    GenericStorage::TIME_STEP;

        // save data
        self.save_hist();

        debug!("pow: {} ,diff:{}, charge: {}", pow, diff, self.charge);

        return diff;
    }
}