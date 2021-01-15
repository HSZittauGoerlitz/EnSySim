// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Controller {
    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Controller {

    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(hist: usize) -> Self {

        let gen_e;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
        } else {
            gen_e = None;
        }

        let controller = Controller {gen_e: gen_e,
                    };
        controller
    }
}

/// Controller
impl Controller {
    pub fn get_chp_state(&mut self) -> bool {
        let state = true;
        state
    }
    /// Calculate current electrical power
    ///
    /// # Arguments
    /// * eg (&f32): Current irradiation on PV module [W/m^2]
    ///
    /// # Returns
    /// * f32: Resulting electrical power [W]
    pub fn step(&mut self) {

    }
}