// external
use pyo3::prelude::*;

use crate::{hist_memory, building};

#[pyclass]
#[derive(Clone)]
pub struct Controller {
    #[pyo3(get)]
    chp_state: bool,
}

#[pymethods]
impl Controller {

    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new() -> Self {

        let chp_state = false;


        let controller = Controller {chp_state: chp_state,
                    };
        controller
    }
}

/// Controller
impl Controller {

    pub fn get_chp_state(&mut self) -> bool {
        return self.chp_state
    }

    /// Decide for chp state for next time step
    /// With this implementation, chp is heat-operated, meaning it produces 
    /// a) if storage content is not enough to deliver enough heat
    /// b) if it ran current time step, but storage is not full yet
    pub fn step(&mut self) {
        if self.chp_state == false {
            self.chp_state = true;
        }
        else {
            self.chp_state = false;
        }   
    }
}