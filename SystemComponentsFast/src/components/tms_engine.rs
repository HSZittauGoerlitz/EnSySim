// external
// external
use pyo3::prelude::*;
use rand::Rng;

use crate::misc::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct TMSEngine {
    #[pyo3(get)]
    pub pow_t: f32, // nominal thermal power of tms engine (charge)
    #[pyo3(get)]
    pub pow_e: f32, // nominal electrical power of tms engine (discharge)

    #[pyo3(get)]
    pub compression_efficiency: f32, // total compression efficiency of tms 0 .. 1
    #[pyo3(get)]
    pub decompression_efficiency: f32, // total decompression efficiency of tms 0 .. 1

    charging_state: f32,  // partial load charge state percentage from 0 to 1
    discharging_state: f32, // partial load discharge state percentage from 0 to 1

    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    con_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    con_t: Option<hist_memory::HistMemory>,
}

#[pymethods]
impl TMSEngine {
    ///  Create TMS engine
    ///  Parameters are power of TMS engine
    ///  The technical design is based on norm heating load and hot water use.
    ///
    /// # Arguments
    /// * power_e (f32): installed electrical tms power [W]
    /// * power_t (f32): installed thermal tms power [W]
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(pow_e: f32, pow_t: f32, hist: usize) -> Self {

        let charging_state = 0.;
        let discharging_state = 0.;

        let mut rng = rand::thread_rng();
        let compression_efficiency: f32 = rng.gen_range(0.8..=0.9);
        let mut rng = rand::thread_rng();
        let decompression_efficiency: f32 = rng.gen_range(0.8..=0.9);

        let (gen_e, gen_t, con_e, con_t) =
            if hist > 0 {
                (Some(hist_memory::HistMemory::new(hist)),
                 Some(hist_memory::HistMemory::new(hist)),
                 Some(hist_memory::HistMemory::new(hist)),
                 Some(hist_memory::HistMemory::new(hist)))
            } else {
                (None, None, None, None)
            };

        TMSEngine {pow_t,
             pow_e,
             charging_state,
             discharging_state,
             compression_efficiency,
             decompression_efficiency,
             gen_e,
             gen_t,
             con_e,
             con_t
             }
    }

    pub fn set_efficiency(&mut self, compression_efficiency: f32, decompression_efficiency: f32) {
        if (compression_efficiency < 0.) | (compression_efficiency > 1.) {
            panic!("Efficiency must be between 0 and 1");
        } else {
            self.compression_efficiency = compression_efficiency;
        }
        if (decompression_efficiency < 0.) | (decompression_efficiency > 1.) {
            panic!("Efficiency must be between 0 and 1");
        } else {
            self.decompression_efficiency = decompression_efficiency;
        }
    }
}

/// TMS engine plant
impl TMSEngine {
    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32, cons_e:&f32, cons_t:&f32) {
        match &mut self.gen_e {
            None => {},
            Some(gen_e) => {
                gen_e.save(*pow_e)
            },
        }
        match &mut self.gen_t {
            None => {},
            Some(gen_t) => {
                gen_t.save(*pow_t)
            }
        }
        match &mut self.con_e {
            None => {},
            Some(con_e) => {
                con_e.save(*cons_e)
            },
        }
        match &mut self.con_t {
            None => {},
            Some(con_t) => {
                con_t.save(*cons_t)
            },
        }
    }

    /// Calculate current electrical and thermal power and electrical and thermal consumption
    ///
    /// # Arguments
    /// * charging_state (bool) 0..1
    /// * discharging_state (bool) 0..1
    ///
    /// # Returns
    /// * (f32, f32, f32, f32): Resulting electrical and thermal power and electrical and thermal consumption [W]
    pub fn step(&mut self, charging_state: &f32, discharging_state: &f32) -> (f32, f32, f32, f32) {

        // update charging and discharging states
        self.charging_state = *charging_state;
        self.discharging_state = *discharging_state;

        // calculate power output and consumption
        let pow_e;
        let pow_t;
        let cons_e;
        let cons_t;

        // charge
        if self.charging_state != 0. {
            cons_e = self.pow_e*self.charging_state;
            cons_t = self.pow_t*self.charging_state;
            pow_e = self.pow_e*self.charging_state*self.compression_efficiency;
            pow_t = self.pow_t*self.charging_state*self.compression_efficiency;
        }

        // discharge
        else if self.discharging_state != 0. {
            cons_e = self.pow_e*self.discharging_state/self.decompression_efficiency;
            cons_t = self.pow_t*self.discharging_state/self.decompression_efficiency;
            pow_e = self.pow_e*self.discharging_state;
            pow_t = self.pow_t*self.discharging_state;
        }

        else {
            cons_e = 0.;
            cons_t = 0.;
            pow_e = 0.;
            pow_t = 0.;
        }

        // save and return data
        self.save_hist(&pow_e, &pow_t, &cons_e, &cons_t);

        return (pow_e, pow_t, cons_e, cons_t);
    }
}