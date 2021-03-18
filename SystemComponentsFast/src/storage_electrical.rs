// external
use pyo3::prelude::*;
use rand::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct ElectricalStorage {
    cap: f32,  // capacity of electrcal storage [J]
    charge: f32,  // charging state of storage [J] -> get_charge()
    state: bool,  // working state of storage
    charging_efficiency: f32,  // 0..1
    discharging_efficiency: f32,  // 0..1
    self_discharge: f32,  // 0..1 percent per ?
    #[pyo3(get)]
    charge_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl ElectricalStorage {
    ///  Create electrical storage with specific capacity
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

        let state = false;
        let charging_efficiency = 1.;
        let discharging_efficiency = 1.;
        let self_discharge = 0.;

        // history
        let charge_e;

        if hist > 0 {
            charge_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            charge_e = None;
        }

        let electrical_storage = ElectricalStorage {cap: cap,
                     charge: charge,
                     state: state,
                     charging_efficiency: charging_efficiency,
                     discharging_efficiency: discharging_efficiency,
                     self_discharge: self_discharge,
                     charge_e: charge_e,
                    };
        electrical_storage
    }
}

/// electrical storage
impl ElectricalStorage {
    pub fn get_charge(& self) -> f32 {
        return self.charge
    }

    fn save_hist_c(&mut self) {
        match &mut self.charge_e {
            None => {},
            Some(charge_e) => {
                charge_e.save(self.charge)
            }
        }
    }

    /// Calculate new charging state
    ///
    /// # Arguments
    /// * 
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self) -> f32 {

        let time_step = 0.25; // ToDo: time step fixed

        // get rid of excess energy
        if self.charge > self.cap {
            self.charge = self.cap;
        }
        // handle empty case 
        if self.charge < 0. {
            warn!("storage is empty and could not supply enough power!");
            self.charge = 0.;
        }

        // save data
        self.save_hist_c();
    }
}