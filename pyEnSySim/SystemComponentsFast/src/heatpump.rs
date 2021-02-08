// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Heatpump {
    //pow_e: f32,  // electrical input power of  heatpump [W]
    #[pyo3(get)]
    pow_t: f32,  // thermalpower of heatpump [W]
    #[pyo3(get)]
    coeffs_Q: Vec<[f32; 6]>, // coefficients for Q correlation (outside temperature)
    #[pyo3(get)]
    coeffs_COP: Vec<[f32; 6]>, // coefficients for COP correlation
    t_supply: f32,  // supply temperature dependent on building
    state: bool,  // on/off switch for heatpump

    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    con_e: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl Heatpump {
    ///  Create heatpump
    ///  Parameters are nominal power of heatpump
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * pow_t (f32): installed thermal power of heatpump [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, t_supply: f32, coeffs_Q: Vec<[f32; 6]>, coeffs_COP: Vec<[f32; 6]>, hist: usize) -> Self {

        // heatpump:
        let pow_t = q_hln;
        let t_supply = t_supply;
        let coeffs_Q = coeffs_Q;
        let coeffs_COP = coeffs_COP;

        let state = false;

        let con_e;
        let gen_t;

        if hist > 0 {
            con_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } else {
            con_e = None;
            gen_t = None;
        }

        let heatpump = Heatpump {pow_t: pow_t,
                     coeffs_Q: coeffs_Q,
                     coeffs_COP: coeffs_COP,
                     t_supply: t_supply,
                     state: state,
                     con_e: con_e,
                     gen_t: gen_t,
                    };
        heatpump
    }
}

/// Heatpump
impl Heatpump {
    fn get_coefficients(&mut self, t_out: &f32) -> ([f32; 6],[f32; 6]) {
        
        let coeffs_Q;
        let coeffs_COP;

        if *t_out < 7. {
            coeffs_Q = self.coeffs_Q[0];
            coeffs_COP = self.coeffs_COP[0];
        }
        else if *t_out < 10. {
            coeffs_Q = self.coeffs_Q[1];
            coeffs_COP = self.coeffs_COP[1];
        }
        else {
            coeffs_Q = self.coeffs_Q[2];
            coeffs_COP = self.coeffs_COP[2];
        }
        return (coeffs_Q, coeffs_COP)
    }

    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.con_e {
            None => {},
            Some(con_e) => {
                con_e.save(*pow_e)
            },
        }
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
    }
    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of CHP plant (on/off)
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool, thermal_load: &f32, t_out: &f32) -> (f32, f32) {

        // update state
        self.state = *state;

        // calculate power output
        let gen_t;
        let con_e;
        let cop;

        let (coeffs_Q, coeffs_COP) = self.get_coefficients(&t_out);
        // ToDo: take modulation into account
        // ToDo: this can be more efficient

        if self.state {
            gen_t = *thermal_load;
            // self.pow_t * (coeffs_Q[0] + coeffs_Q[1]*self.t_supply + coeffs_Q[2]*t_out + coeffs_Q[3]*self.t_supply*t_out + coeffs_Q[4]*f32::powf(self.t_supply,2.) + coeffs_Q[5]*f32::powf(*t_out, 2.));
            cop = coeffs_COP[0] + coeffs_COP[1]*self.t_supply + coeffs_COP[2]*t_out + coeffs_COP[3]*self.t_supply*t_out + coeffs_COP[4]*f32::powf(self.t_supply,2.) + coeffs_COP[5]*f32::powf(*t_out, 2.);
            con_e = gen_t / cop;
        }
        else {
            gen_t = 0.0;
            con_e = 0.0;
        }

        // save and return data
        self.save_hist(&con_e, &gen_t);

        return (con_e, gen_t);
    }
}