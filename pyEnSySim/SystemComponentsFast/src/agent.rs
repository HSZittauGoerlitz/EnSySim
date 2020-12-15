// external
use pyo3::prelude::*;
use rand::Rng;
use rand_distr::{Distribution, Beta, Gamma, Normal, FisherF};

#[pyclass]
#[derive(Clone, Copy)]
pub struct Agent {
    a_type: usize,  // 0: PHH, 1: BSLa, 2: BSLc
    #[pyo3(get)]
    demand_apv: f32,
    #[pyo3(get)]
    coc: f32,
}

#[pymethods]
impl Agent {
    /// Create Agent
    ///
    /// # Arguments
    /// * a_type (usize): Type of agent (0: PHH, 1: BSLa, 2: BSLc)
    ///
    /// "PHH": private household
    /// "BSLa": Small Agriculture business with
    ///         electrical standard load profile and
    ///         thermal phh standard load profile
    /// "BSLc": Common business with
    ///         electrical standard load profile and
    ///         thermal phh standard load profile
    #[new]
    pub fn new(a_type: usize) -> Self {
        if a_type > 2 {
            panic!("Unknown agent type");
        }

        let mut agent = Agent {a_type: a_type,
                               coc: 0.,
                               demand_apv: 0.
                               };
        agent.get_apv_demand();
        agent.get_coc();
        agent
    }
}

/// Agent to simulate human consumption behaviour
impl Agent {
    /// Calculate the demand for PV area to cover a part of the
    /// electrical energy consumption.
    /// Determine between PHH and BSL, since they have different
    /// underlying statistics
    fn get_apv_demand(&mut self) {
        let mut rng = rand::thread_rng();

        let rnd: f32 = rng.gen();

        self.demand_apv = rng.gen_range(0.8, 1.2);

        if self.a_type == 0 {
            if rnd < 0.7 {
                let dist = Normal::new(0.3, 0.025).unwrap();
                self.demand_apv *= dist.sample(&mut rng);
                return ();
            }
        }
        let dist = FisherF::new(7.025235971695065, 2205.596792511838).unwrap();
        self.demand_apv *= dist.sample(&mut rng) * 0.299704041191481 + 0.1;
    }

    /// Get COC factor of agent
    /// Determine between PHH and BSL, since they have different
    /// underlying statistics
    fn get_coc(&mut self) {
        let mut coc: f32 = 0.;
        let mut rng = rand::thread_rng();

        if self.a_type == 0 {
            // Beta distribution with a, b
            let dist = Beta::new(3.944677863332723, 2.638609989052125).unwrap();
            let mut i = 0;
            while i < 10 {
                coc = dist.sample(&mut rng) * 5.;
                if coc >= 1. {break;}
                i += 1;
            }
        } else {
            // Gamma sistribution with shape, scale
            let dist = Gamma::new(1.399147113755027, 1.876519590091970).unwrap();
            let mut i = 0;
            while i < 10 {
                coc = dist.sample(&mut rng) * 1.;
                if coc >= 1. {break;}
                i += 1;
            }
        }

        if coc < 1. {
            self.coc = 1.;
        } else {
            self.coc = coc;
        }
    }

    /// Calculate agents actual hot water demand
    /// in relation to current hot water profile value.
    /// For the calculation a regression model,
    /// deviated off destatis data, is used.
    ///
    /// # Arguments
    /// * hw_profile (f32): Actual hw profile value [W]
    ///
    /// # Returns
    /// * f32: agents hot water demand [W]
    fn get_hot_water_demand(&self, hw_profile: &f32) -> f32 {
        let mut rng = rand::thread_rng();
        let r_f: f32 = rng.gen_range(0.8, 1.2);

        (684.7 * hw_profile + 314.4) * r_f
    }

    /// Calculate and return current energy load
    ///
    /// # Arguments
    ///    slp_data ([f32; 3]): Standard load Profile of all agent types
    ///    hw_profile (f32): Actual hw profile value [W]
    ///
    /// # Returns
    /// * (f32, f32): Currend electrical and thermal energy demand [W]
    pub fn step(&self, slp_data: &[f32; 3], hw_profile: &f32) -> (f32, f32) {
        let mut rng = rand::thread_rng();

        let electrical = slp_data[self.a_type] * rng.gen_range(0.8, 1.2);
        let thermal = self.get_hot_water_demand(hw_profile);

        (electrical, thermal)
    }

    // Access to attributes
    pub fn coc(&self) -> &f32 {
        &self.coc
    }

    pub fn demand_apv(&self) -> &f32 {
        &self.demand_apv
    }
}