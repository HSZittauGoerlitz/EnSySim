// external
use pyo3::prelude::*;

use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct Heatpump {
    //pow_e: f32,  // electrical input power of  heatpump [W]
    #[pyo3(get)]
    pow_t: f32,  // thermalpower of heatpump [W]
    state: bool,  // on/off switch for heatpump
    t_supply: f32,

    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    con_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    cop_hist: Option<hist_memory::HistMemory>,
}

fn cop_from_coefficients(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {
    
    let coeffs_cop;
    if pow_t < &18000. {
        if t_out < &7. {
            coeffs_cop = [5.398, -0.05601, 0.14818, -0.00185, 0., 0.0008];
        }
        else if t_out < &10. {
            coeffs_cop = [6.22734, -0.07497, 0.07841, 0., 0., 0.];
        }
        else {
            coeffs_cop = [5.59461, -0.0671, 0.17291, -0.00097, 0., -0.00206];
        }
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_cop = [4.79304, -0.04132, 0.05651, 0., 0., 0.];
        }
        else if t_out < &10. {
            coeffs_cop = [6.34439, -0.1043, 0.0751, -0.00016, 0.00059, 0.];
        }
        else {
            coeffs_cop = [5.07629, -0.04833, 0.09969, -0.00096, 0.00009, 0.];
        }
    }
    else {
        if t_out < &7. {
            coeffs_cop = [6.28133, -0.10087, 0.11251, -0.00097, 0.00056, 0.00069];
        }
        else if t_out < &10. {
            coeffs_cop = [6.23384, -0.09963, 0.11295, -0.00061, 0.00052, 0.];
        }
        else {
            coeffs_cop = [5.0019, -0.04138, 0.10137, -0.00112, 0., 0.00027];
        }
    }
    let cop = coeffs_cop[0] + coeffs_cop[1]*t_supply
              + coeffs_cop[2]*t_out + coeffs_cop[3]*t_supply*t_out 
              + coeffs_cop[4]*f32::powf(*t_supply,2.) 
              + coeffs_cop[5]*f32::powf(*t_out, 2.);
    cop
}

fn q_from_coefficients(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {
    
    let coeffs_q;
    if pow_t < &18000. {
        if t_out < &7. {
            coeffs_q = [1.04213, -0.00234, 0.03152, -0.00019, 0., 0.];
        }
        else if t_out < &10. {
            coeffs_q = [1.02701, -0.00366, 0.03202, 0.00003, 0., 0.];
        }
        else {
            coeffs_q = [0.81917, -0.00301, 0.0651, -0.00003, 0., -0.00112];
        }
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_q = [1.03825, -0.00223, 0.02272, 0., 0., 0.];
        }
        else if t_out < &10. {
            coeffs_q = [0.93526, -0.0005, 0.03926, -0.00021, 0., 0.];
        }
        else {
            coeffs_q = [0.79796, 0.00005, 0.05928, -0.00026, 0., -0.00066];
        }
    }
    else {
        if t_out < &7. {
            coeffs_q = [1.10902, -0.00478, 0.02136, 0.00019, 0., 0.];
        }
        else if t_out < &10. {
            coeffs_q = [1.08294, -0.00438, 0.03386, 0., 0., 0.];
        }
        else {
            coeffs_q = [1.10262, -0.00316, 0.0295, -0.00009, 0., 0.00008];
        }
    }
    let q = (coeffs_q[0] + coeffs_q[1]*t_supply
              + coeffs_q[2]*t_out + coeffs_q[3]*t_supply*t_out 
              + coeffs_q[4]*f32::powf(*t_supply,2.) 
              + coeffs_q[5]*f32::powf(*t_out, 2.));
    q
}

#[pymethods]
impl Heatpump {
    ///  Create heatpump
    ///  Parameters are nominal power of heatpump
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * power_t (f32): installed thermal power of heatpump [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(power_t: f32, t_supply: f32, hist: usize) -> Self {

        // heatpump:
        let pow_t = power_t;
        let t_supply = t_supply;
        let state = false;

        let con_e;
        let gen_t;
        let cop_hist;

        if hist > 0 {
            con_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
            cop_hist = Some(hist_memory::HistMemory::new(hist));
        } else {
            con_e = None;
            gen_t = None;
            cop_hist = None;
        }

        let heatpump = Heatpump {pow_t: pow_t,
                     state: state,
                     t_supply: t_supply,
                     con_e: con_e,
                     gen_t: gen_t,
                     cop_hist: cop_hist,
                    };
        heatpump
    }
}

/// Heatpump
impl Heatpump {

    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32, cop: &f32) {
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
        match &mut self.cop_hist {
            None => {},
            Some(cop_hist) => {
                cop_hist.save(*cop)
            }
        }
    }
    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of heatpump (on/off)
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, state: &bool, t_out: &f32) 
    -> (f32, f32) {

        // update state
        self.state = *state;

        // calculate power output
        let gen_t;
        let con_e;
        let cop;

        if *state {
            gen_t =  self.pow_t * q_from_coefficients(&self.pow_t,
                                                      t_out,
                                                      &self.t_supply);
            cop = cop_from_coefficients(&self.pow_t, t_out, &self.t_supply);
            con_e = gen_t / cop;
        }
        else {
            gen_t = 0.;
            con_e = 0.;
            cop = -1.;
        }
        // ToDo: take modulation into account

        // save and return data
        self.save_hist(&con_e, &gen_t, &cop);

        return (con_e, gen_t);
    }
}