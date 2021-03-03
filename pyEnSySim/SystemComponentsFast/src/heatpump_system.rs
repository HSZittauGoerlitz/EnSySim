// external
use pyo3::prelude::*;
use log::{warn};

use crate::boiler::Boiler;
use crate::heatpump::Heatpump;
use crate::storage_thermal::ThermalStorage;
use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct HeatpumpSystem {
    heatpump: Heatpump,  // heatpump
    storage: ThermalStorage,  // thermal storage
    boiler: Boiler,  // peak load boiler

    #[pyo3(get)]
    gen_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

fn average(numbers: &[f32]) -> f32 {
    let average: f32 = numbers.iter().sum() / numbers.len() as f32;
    average
}

fn heatpump_coefficients_cop(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {
    
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
    else if pow_t < &35000 {
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

#[pymethods]
impl HeatpumpSystem {
    ///  Create heatpump system with thermal storage and boiler
    ///  The technical design is based on norm heating load.
    ///
    /// # Arguments
    /// * q_hln (f32): norm heating load of building
    /// * seas_perf_fac (f32): minimum allowed seasonal performance factor, 
    ///                        dependent on building (3.5 or 4.5)
    /// * t_supply (f32): supply temperature, dependent on building 
    /// * t_ref (Vec<[f32; 365]>): temperatures of reference year 
    ///                            (DWD, 1995-2012)
    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(q_hln: f32, seas_perf_fac: f32, t_supply: f32, 
               t_ref: &Vec<[f32; 8760]>, hist: usize) -> Self {

        // start with maximum thermal power
        // use 6h blocking time by electricity provider
        // ToDo: water heating time
        let pow_t = q_hln * 24. / (24.-6.);
        let t_heat = 15.;

        let mut heating_days: [bool; 8760] = [false; 8760];

        // get heating days bools (hourly)
        for i in 0..=364 {
            let idx = (i*24)..(i*24+24);
            let t_day = &t_ref[idx];
            if average(t_day) < t_heat {
                heating_days[idx].fill(true);
            }
        }

        let mut cops: [f32; 8760];

        // wenn true in heating days:
        // for all remaining (heating days subtracted)
        for (idx, t_out) in t_ref.iter().enumerate() {
            if heating_days[idx] {
                cops[idx] = heatpump_coefficients_cop(&pow_t, 
                                                      &t_out, &t_supply);
            }
        }
            
        let cop_mean = average(&cops);
        let mut _t = t_ref.iter().min();
        let t_min;
        match _t {
            Some(min) => t_min = min,
            None      => warn!("min not found"),
        }
        // coefficients are not dependend on power class for now
        while cop_mean < seas_perf_fac {
            t_min = &(t_min + 1.);
            for (idx, temp) in t_ref.iter().enumerate() {
                if temp < t_min {
                    heating_days[idx] = false;
                }
            }
            let mut i = 0;
            let cop_values = cops.retain(|_| (heating_days[i]), i += 1).0;
            cop_mean = average(cop_values);
        }

        // update installed power at minimal working temperature
        pow_t = (-q_hln/t_heat) * t_min + q_hln;



        // calculate predicted seasonal performance factor with
        // - outside temperatures
        // - supply temperature
        // - coefficients of performance

        // heatpump
        let heatpump = Heatpump::new(pow_t, t_supply, hist);

        // boiler
        let boiler = Boiler::new(q_hln - pow_t, hist);

        // thermal storage:
        // 50l~kg per kW thermal generation, 40K difference 
        // -> 60°C, c_water = 4.184 KJ(kg*K)
        let models: [f32;11] = [200., 300., 400., 500., 600., 750., 950., 
                                1500., 2000., 3000., 5000.];
        let mut diffs: [f32;11] = [0.;11];
        let exact = 25.0 * 50.0; // kW * l/kW
        
        for (pos, model) in models.iter().enumerate() {
            diffs[pos] = (exact - model).abs();
        }
        
        let index = min_index(&diffs);
        // ToDo: bring to helper.rs file
        fn min_index(array: &[f32]) -> usize {
            let mut i = 0;
        
            for (j, &value) in array.iter().enumerate() {
                if value < array[i] {
                    i = j;
                }
            }
            i
        }
        let volume = models[index];
        let cap = volume * 4.184*1000. * 40.;

        let storage = ThermalStorage::new(cap, hist);


        let gen_e;
        let gen_t;

        if hist > 0 {
            gen_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        } 
        else {
            gen_e = None;
            gen_t = None;
        }

        let heatpump_system = HeatpumpSystem {heatpump: heatpump,
                     storage: storage,
                     boiler: boiler,
                     gen_e: gen_e,
                     gen_t: gen_t,
                    };
        heatpump_system
    }
}

/// CHP plant
impl HeatpumpSystem {
    fn save_hist(&mut self, pow_e: &f32, pow_t: &f32) {
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
    }

    /// Calculate current electrical and thermal power
    ///
    /// # Arguments
    /// * state (&bool): Current state of CHP plant (on/off)
    /// * thermal_load (&f32): thermal load of building this time step
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self, 
                state: &bool,
                thermal_load: &f32,
                t_out: &f32) -> (f32, f32) {

    }
}