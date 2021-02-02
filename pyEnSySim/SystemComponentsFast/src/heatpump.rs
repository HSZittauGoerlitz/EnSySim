// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Heatpump {
    //pow_e: f32,  // electrical input power of  heatpump [W]
    pow_t: f32,  // thermalpower of heatpump [W]
    coeffs: Vec<[f32; 6]>, // coefficants following: Thomas Kemmler und Bernd Thomas. „Simulation von Wärmepumpensystemem auf der Grundlage von Korrelationsfunktionen für die Leistungsdaten der Wärmepumpe“, 2020.
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
    pub fn new(power_t: f32, t_supply: f32, hist: usize) -> Self {

        // heatpump:
        let pow_t = power_t;
        let t_supply = t_supply;
        let coeffs = [1., -0.002, 0.03, -0.0002, 0., 0.] //ToDo: read from file, dependent on t_out, power_t

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
                     coeffs: coeffs,
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
    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
        match &mut self.gen_e {
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
        if self.state {
            gen_t = self.pow_t * (self.coeff[0] + self.coeff[1]*self.t_supply + self.coeff[2]*t_out + self.coeff[3]*self.t_supply*t_out + self.coeff[4]*self.t_supply**2 + self.coeff[5]*t_out**2);
            con_e = (self.coeff[0] + self.coeff[1]*self.t_supply + self.coeff[2]*t_out + self.coeff[3]*self.t_supply*t_out);
            cop = (self.coeff[0] + self.coeff[1]*self.t_supply + self.coeff[2]*t_out + self.coeff[3]*self.t_supply*t_out + self.coeff[4]*self.t_supply**2 + self.coeff[5]*t_out**2)
        }
        else {
            pow_t = 0.0;
            pow_e = 0.0;
        }

        // save and return data
        self.save_hist(&con_e, &gen_t);

        return (-con_e, gen_t);
    }
}