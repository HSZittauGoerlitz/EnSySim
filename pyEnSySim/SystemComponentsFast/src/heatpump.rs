// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Heatpump {
    //pow_e: f32,  // electrical input power of  heatpump [W]
    pow_t: f32,  // thermalpower of heatpump [W]
    coeffs_Q: [f32; 6], // coefficants following: Thomas Kemmler und Bernd Thomas. „Simulation von Wärmepumpensystemem auf der Grundlage von Korrelationsfunktionen für die Leistungsdaten der Wärmepumpe“, 2020.
    coeffs_COP: [f32; 6], // coefficants following: Thomas Kemmler und Bernd Thomas. „Simulation von Wärmepumpensystemem auf der Grundlage von Korrelationsfunktionen für die Leistungsdaten der Wärmepumpe“, 2020.
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
    pub fn new(q_hln: f32, t_supply: f32, coeffs: Vec<[Vec<[f32; 6]>;6]>, hist: usize) -> Self {

        // heatpump:
        let pow_t = q_hln;
        let t_supply = t_supply;
        let coeffs_Q = [1., -0.002, 0.03, -0.0002, 0., 0.]; //ToDo: read from file, dependent on t_out, power_t
        let coeffs_COP = [5.4, -0.06, 0.15, -0.002, 0., 0.];//do it during step(), d,e can be ignored

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
    fn get_coeffs(&mut self, t_out: &f32) {
        if *t_out < 7. {
            // ToDo: get coefficants from h5 file, depending on self.pow_t and t_out
        }
        else if *t_out < 10. {

        }
        else {
            
        }
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
    pub fn step(&mut self, state: &bool, t_out: &f32) -> (f32, f32) {

        // update state
        self.state = *state;

        // calculate power output
        let gen_t;
        let con_e;
        let cop;

        //self.get_coeffs(&t_out); // ToDo: write function

        if self.state {
            gen_t = self.pow_t * (self.coeffs_Q[0] + self.coeffs_Q[1]*self.t_supply + self.coeffs_Q[2]*t_out + self.coeffs_Q[3]*self.t_supply*t_out + self.coeffs_Q[4]*f32::powf(self.t_supply,2.) + self.coeffs_Q[5]*f32::powf(*t_out, 2.));
            cop = self.coeffs_COP[0] + self.coeffs_COP[1]*self.t_supply + self.coeffs_COP[2]*t_out + self.coeffs_COP[3]*self.t_supply*t_out + self.coeffs_COP[4]*f32::powf(self.t_supply,2.) + self.coeffs_COP[5]*f32::powf(*t_out, 2.);
            con_e = gen_t / cop;
        }
        else {
            gen_t = 0.0;
            con_e = 0.0;
        }

        // save and return data
        self.save_hist(&con_e, &gen_t);

        return (-con_e, gen_t);
    }
}