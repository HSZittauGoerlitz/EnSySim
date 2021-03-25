// external
use pyo3::prelude::*;
use log::{debug};

use crate::boiler::Boiler;
use crate::heatpump::Heatpump;
use crate::generic_storage::GenericStorage;
use crate::hist_memory;

#[pyclass]
#[derive(Clone)]
pub struct HeatpumpSystem {
    #[pyo3(get)]
    heatpump: Heatpump,  // heatpump
    #[pyo3(get)]
    storage: GenericStorage,  // thermal storage
    #[pyo3(get)]
    boiler: Boiler,  // peak load boiler

    // Controller variables
    boiler_state: bool,
    hp_state: bool,

    #[pyo3(get)]
    con_e: Option<hist_memory::HistMemory>,
    #[pyo3(get)]
    gen_t: Option<hist_memory::HistMemory>,
}

fn average(numbers: &[f32]) -> f32 {
    let mut average: f32 = numbers.iter().sum();
    average = average / numbers.len() as f32;
    average
}

/* fn average_bool_select(numbers: &[f32], bool_select: &[bool]) -> f32 {
    let mut sum = 0.;
    let mut count = 0;
    for (idx, sel) in bool_select.iter().enumerate() {
        if *sel {
            sum += numbers[idx];
            count += 1;
        }
    }
    sum / (count as f32)
} */

fn average_bool_select_weighted(numbers: &[f32], weights: &[f32],
                                bool_select: &[bool]) -> f32 {
    let mut sum = 0.;
    let mut weights_sum = 0.;
    for (idx, sel) in bool_select.iter().enumerate() {
        if *sel {
            sum += numbers[idx] * weights[idx];
            weights_sum += weights[idx];
        }
    }
    sum  / weights_sum
}

fn cop_from_coefficients(pow_t: &f32, t_out: &f32, t_supply: &f32) -> f32 {

    let coeffs_cop;
    if pow_t < &18000. {
        if t_out < &7. {
            coeffs_cop = [5.398, -0.05601, 0.14818, -0.00185, 0., 0.0008];}
        else if t_out < &10. {
            coeffs_cop = [6.22734, -0.07497, 0.07841, 0., 0., 0.];}
        else {
            coeffs_cop = [5.59461, -0.0671, 0.17291, -0.00097, 0., -0.00206];}
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_cop = [4.79304, -0.04132, 0.05651, 0., 0., 0.];}
        else if t_out < &10. {
            coeffs_cop = [6.34439, -0.1043, 0.0751, -0.00016, 0.00059, 0.];}
        else {
            coeffs_cop = [5.07629, -0.04833, 0.09969, -0.00096, 0.00009, 0.];}
    }
    else {
        if t_out < &7. {
            coeffs_cop = [6.28133, -0.10087, 0.11251, -0.00097, 0.00056,
                          0.00069];}
        else if t_out < &10. {
            coeffs_cop = [6.23384, -0.09963, 0.11295, -0.00061, 0.00052, 0.];}
        else {
            coeffs_cop = [5.0019, -0.04138, 0.10137, -0.00112, 0., 0.00027];}
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
            coeffs_q = [1.04213, -0.00234, 0.03152, -0.00019, 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [1.02701, -0.00366, 0.03202, 0.00003, 0., 0.];}
        else {
            coeffs_q = [0.81917, -0.00301, 0.0651, -0.00003, 0., -0.00112];}
    }
    else if pow_t < &35000. {
        if t_out < &7. {
            coeffs_q = [1.03825, -0.00223, 0.02272, 0., 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [0.93526, -0.0005, 0.03926, -0.00021, 0., 0.];}
        else {
            coeffs_q = [0.79796, 0.00005, 0.05928, -0.00026, 0., -0.00066];}
    }
    else {
        if t_out < &7. {
            coeffs_q = [1.10902, -0.00478, 0.02136, 0.00019, 0., 0.];}
        else if t_out < &10. {
            coeffs_q = [1.08294, -0.00438, 0.03386, 0., 0., 0.];}
        else {
            coeffs_q = [1.10262, -0.00316, 0.0295, -0.00009, 0., 0.00008];}
    }
    let q = coeffs_q[0] + coeffs_q[1]*t_supply
              + coeffs_q[2]*t_out + coeffs_q[3]*t_supply*t_out
              + coeffs_q[4]*f32::powf(*t_supply,2.)
              + coeffs_q[5]*f32::powf(*t_out, 2.);
    q
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
               t_ref: Vec<f32>, hist: usize) -> Self {

        // start with full building supply
        // use 6h blocking time by electricity provider
        // ToDo: account for drinking water heating time
        // account for blocking times in final result
        let t_out_n = -13.8; // East
        let mut pow_t = q_hln * 24. / (24.-6.) /
                        cop_from_coefficients(&q_hln, &t_out_n, &t_supply);

        // reference temperature for heating days
        let t_heat = 15.;
        // local copy neccessary
        let reference_temperatures = t_ref.to_vec();
        // get heating days bools (hourly)
        let mut heating_days: [bool; 8760] = [false; 8760];
        for i in 0..=364 {
            // ToDo: idx created twice
            let idx = (i*24)..(i*24+24);
            let t_day = &reference_temperatures[idx];
            let idx = (i*24)..(i*24+24);
            if average(t_day) < t_heat {
                heating_days[idx].fill(true);
            }
        }

        // calculate COP and power factor for all hours in heating days
        let mut cops: [f32; 8760] = [0.; 8760];
        let mut qs: [f32; 8760] = [0.; 8760];
        for (idx, t_out) in reference_temperatures.iter().enumerate() {
            if heating_days[idx] {
                cops[idx] = cop_from_coefficients(&pow_t, &t_out, &t_supply);
                qs[idx] = q_from_coefficients(&pow_t, &t_out, &t_supply);
            }
        }

        // get minimum temperature from reference year
        let mut t_min = reference_temperatures[0];
        for value in &reference_temperatures {
            if *value < t_min {
                t_min = *value;
            }
        }

        // introduce seasonal performance factor as mean of COPS
        let mut cop_mean = -1.;
        // needed heating power for each hour
        let mut pow_heat: [f32; 8760] = [0.; 8760];
        let intercept = (t_heat/(t_heat-t_out_n)) * q_hln;

        // increase lower bound of heatpump working temperatures till mean
        // COP satisfies minimum seasonal performance factor
        let mut iter_count = 0.;
        while cop_mean < seas_perf_fac {
            // update bool vector for hour selection
            debug!("iteration {}", iter_count);
            // increase lower bound of heatpump working temperature
            if iter_count > 0. {
                t_min = t_min + 1.;
            }

            for (idx, temp) in reference_temperatures.iter().enumerate() {
                if *temp < t_min {
                    heating_days[idx] = false;
                }
                if heating_days[idx] == true {
                    // calculate needed heating power for this hour
                    pow_heat[idx] = (-q_hln / (t_heat-t_out_n)) *
                                     temp + intercept;
                }
            }
            // introduce weights to take into account over- and undersupply
            // during this hour
            let mut weights: [f32; 8760] = [1.; 8760];
            // calculate installed heatpump power based on heat needed at
            //  minimum working temperature and power factor
            pow_t = ((-q_hln / (t_heat-t_out_n)) * t_min + intercept) /
                      q_from_coefficients(&pow_t, &t_min, &t_supply);
            // calculate weights
/*             for (idx, value) in heating_days.iter().enumerate() {
                let mut div = 0.;
                if *value == true {
                    div = pow_heat[idx] / (pow_t * qs[idx]);

                    if div > 1. {
                        weights[idx] = 1.;
                    }
                    else {
                        weights[idx] = div;
                    }
                }
            } */
            // calculate mean cop
            cop_mean = average_bool_select_weighted(&cops, &weights,
                                                    &heating_days);
            iter_count += 1.;

            let min_cop = cop_from_coefficients(&pow_t, &t_min, &t_supply);
            let min_q = q_from_coefficients(&pow_t, &t_min, &t_supply);
            debug!("calculated mean cop: {},
                    minimum cop: {},
                    minimum power factor: {}",
                    cop_mean, min_cop, min_q);

            debug!("net power: {}W, for
                   minimum temperature: {}°C and
                   supply temperature: {}°C
                   max heating load: {}W,
                   corresponding heating power: {}W",
                   &pow_t, &t_min, &t_supply, &q_hln,
                   &(pow_t * min_q));
        }
        let min_cop = cop_from_coefficients(&pow_t, &t_min, &t_supply);
        let min_q = q_from_coefficients(&pow_t, &t_min, &t_supply);
        debug!("calculated mean cop: {},
                minimum cop: {},
                minimum power factor: {}",
                cop_mean, min_cop, min_q);

        debug!("net power: {}W, for
               minimum temperature: {}°C and
               supply temperature: {}°C
               max heating load: {}W,
               corresponding heating power: {}W",
               &pow_t, &t_min, &t_supply, &q_hln,
               &(pow_t * min_q));
 //debug!("{}", cop_from_coefficients(&7822.9, &-11.7, &35.));

        // create heatpump
        let heatpump = Heatpump::new(pow_t, t_supply, hist);

        // create boiler based on missing power
        let boiler = Boiler::new(q_hln - pow_t * min_q, hist);

        // thermal storage:
        // 50l~kg per kW thermal generation, 40K difference
        // -> 60°C, c_water = 4.184 KJ(kg*K)
        let models: [f32;11] = [200., 300., 400., 500., 600., 750., 950.,
                                1500., 2000., 3000., 5000.];
        let mut diffs: [f32;11] = [0.;11];
        let exact = pow_t * 50.0; // kW * l/kW

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
        let temp_diff = t_supply + 5. - 20.; // 5°C spread, 20°C room temperature
        let cap = volume * 4.184*1000. * temp_diff / 3600.;

        // dummy parameters for now
        let storage = GenericStorage::new(cap,
                                          0.95,
                                          0.95,
                                          0.05,
                                          q_hln,
                                          hist);

        let con_e;
        let gen_t;

        if hist > 0 {
            con_e = Some(hist_memory::HistMemory::new(hist));
            gen_t = Some(hist_memory::HistMemory::new(hist));
        }
        else {
            con_e = None;
            gen_t = None;
        }

        let heatpump_system = HeatpumpSystem {heatpump: heatpump,
                                              storage: storage,
                                              boiler: boiler,
                                              boiler_state: false,
                                              hp_state: false,
                                              con_e: con_e,
                                              gen_t: gen_t,
                                              };
        heatpump_system
    }
}


impl HeatpumpSystem {
    // Control Parameter
    const STORAGE_LEVEL_1: f32 = 0.95;
    const STORAGE_LEVEL_2: f32 = 0.6;
    const STORAGE_LEVEL_3: f32 = 0.3;
    const STORAGE_LEVEL_4: f32 = 0.2;

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
    /// * thermal_load (&f32): thermal load of building this time step
    /// * t_out (&f32): Outside temperature [degC]
    ///
    /// # Returns
    /// * (f32, f32): Resulting electrical and thermal power [W]
    pub fn step(&mut self,
                thermal_load: &f32,
                t_out: &f32) -> (f32, f32) {

        let time_step = 0.25; // ToDo: time step fixed

        let storage_state = self.storage.get_relative_charge();
        debug!("storage state: {}", storage_state);

        if storage_state <= HeatpumpSystem::STORAGE_LEVEL_4 {
            self.boiler_state = true;
            self.hp_state = true;
        }
        else if (storage_state <= HeatpumpSystem::STORAGE_LEVEL_3) &
                (self.hp_state == false) {
            self.boiler_state = false;
            self.hp_state = true;
        }
        else if (storage_state >= HeatpumpSystem::STORAGE_LEVEL_2) &
                (self.boiler_state == true) {
            self.boiler_state = false;
            self.hp_state = true;
        }
        else if storage_state >= HeatpumpSystem::STORAGE_LEVEL_1 {
            self.hp_state = false;
            self.boiler_state = false;
        }

        let (con_e, chp_t) = self.heatpump.step(&self.hp_state, t_out);
        let boiler_t = self.boiler.step(&self.boiler_state);

        let pow_t = chp_t + boiler_t;
        let storage_t = pow_t - thermal_load;

        // call storage step -> check if all energy could be processed
        let storage_diff = self.storage.step(&storage_t);

        // save production data
        self.save_hist(&con_e, &pow_t);

        // return supply data
        return (con_e, thermal_load + storage_diff);
    }
}