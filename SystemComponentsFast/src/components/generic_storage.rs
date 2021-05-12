// external
use pyo3::prelude::*;
use rand::prelude::*;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct GenericStorage {
    #[pyo3(get)]
    cap: f32,  // capacity of storage [Wh]
    #[pyo3(get)]
    charge: f32,  // charging state of storage [Wh]
    #[pyo3(get)]
    charging_efficiency: f32,  // 0..1
    #[pyo3(get)]
    discharging_efficiency: f32,  // 0..1
    #[pyo3(get)]
    self_discharge: f32,  // 0.. [1/h]
    // ToDo: cycle decay (only electrical)
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
    /// * charging_efficiency (f32): Efficiency of charging storage [-]
    /// * discharging_efficiency (f32): Efficiency of discharging storage [-]
    /// * self_discharge:(f32): Self discharge of storage [1/h]
    /// * pow_max (f32): Max. power flow in or out of storage [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(cap: f32,
               charging_efficiency: f32,
               discharging_efficiency: f32,
               self_discharge:f32,
               pow_max: f32,
               hist: usize) -> Self {

        if cap < 0. {
            panic!("Storage capacity must be greater than 0");
        }

        if (charging_efficiency < 0.) | (charging_efficiency > 1.) {
            panic!("Charging efficiency must be between 0 and 1")
        }
        if (discharging_efficiency < 0.) | (discharging_efficiency > 1.) {
            panic!("Discharging efficiency must be between 0 and 1")
        }
        if self_discharge < 0. {
            panic!("Self discharge must be at least 0/h")
        }

        if pow_max < 0. {
            panic!("Max. storage power must be greater than 0");
        }


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
    /// * (f32, f32):
    ///   - Power used for charging [W]
    ///   - Losses during charge [W]
    fn charge_storage(& mut self, charge_power: &f32) -> (f32, f32) {
        // check for a) maximum power flow and b) free storage capacity
        let mut diff = *charge_power - self.pow_max;
        let resulting_charge_power;

        if diff > 0. {
            resulting_charge_power = self.pow_max;
        } else {
            resulting_charge_power = *charge_power;
            diff = 0.;
        }

        let f_charge_loss = 1. - self.charging_efficiency;
        let mut charge_loss = resulting_charge_power * f_charge_loss;
        let charge_old = self.charge;
        self.charge += (resulting_charge_power - charge_loss) *
                       GenericStorage::TIME_STEP;

        if self.charge > self.cap {
            diff += (self.charge - self.cap) / GenericStorage::TIME_STEP +
                    charge_loss;  // revert subtraction of losses
            // recalculate losses in relation to actual charge power
            charge_loss = (self.cap - charge_old) / GenericStorage::TIME_STEP *
                          f_charge_loss;
            diff -= charge_loss;
            self.charge = self.cap;
        }
        // diff didn´t fit into storage -> positive
        return (diff, charge_loss)
    }

    /// Discharge storage with given power
    ///
    /// Discharge Power is negative!
    ///
    /// # Arguments
    /// * discharge_power (&f32): Power requested during time step [W]
    ///
    /// # Returns
    /// * (f32, f32):
    ///   - Power provided by storage [W]
    ///   - Losses during discharge [W]
    fn discharge_storage(&mut self, discharge_power: &f32) -> (f32, f32) {
        // check for a) maximum power flow and b) available storage content
        let mut diff = *discharge_power + self.pow_max;
        let resulting_discharge_power;

        if diff < 0. {
            resulting_discharge_power = -self.pow_max;
        } else {
            resulting_discharge_power = *discharge_power;
            diff = 0.;
        }

        let f_discharge_loss = 1. - self.discharging_efficiency;
        let mut discharge_loss = resulting_discharge_power * f_discharge_loss;
        // The complete energy will be subtracted from storage
        // Additionally the losses have to be subtracted
        // that way the storage can fullfill the requested demand
        // discharge power and loss are negative
        let charge_old = self.charge;
        self.charge += (resulting_discharge_power + discharge_loss) *
                       GenericStorage::TIME_STEP;

        if  self.charge < 0. {
            diff += self.charge / GenericStorage::TIME_STEP - discharge_loss;
            // recalculate losses in relation to actual discharge power
            discharge_loss = -charge_old / GenericStorage::TIME_STEP *
                             f_discharge_loss;
            // losses couldn't be provided by storage -> add to diff
            diff += discharge_loss;
            self.charge = 0.;
        }
        // diff couldn't be supplied -> negative
        return (diff, -discharge_loss)
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
    /// * (f32, f32):
    ///   - Not received or delivered power [W], difference between
    ///     requested and handled power
    ///   - Losses due charging/discharging as well as self discharge [W]
    pub fn step(&mut self, pow: &f32) -> (f32, f32)
    {
        let self_loss_start = self.charge * self.self_discharge; // W

        let (diff, loss) =
          if *pow > 0. {
              self.charge_storage(pow)
          }
          else if *pow < 0. {
              self.discharge_storage(pow)
          } else {
              (0., 0.)
          };

        let self_loss_end = self.charge * self.self_discharge; // W
        let self_loss = 0.5*self_loss_start + 0.5*self_loss_end;

        self.charge = self.charge - self_loss*GenericStorage::TIME_STEP;

        // save data
        self.save_hist();

        return (diff, loss + self_loss);
    }
}