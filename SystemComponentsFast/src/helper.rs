// Parameter used by helper functions
static C_WATER:f32 = 1.162;  // (Wh) / (kg K)
static RHO_WATER:f32 = 983.2;  // kg / m^3
// Available storage volumes in m^3
static MODELS: [f32; 11] = [0.2, 0.3, 0.4, 0.5, 0.6, 0.75,
                            0.95, 1.5, 2., 3., 5.];

/// Find first occurrence of min value in given float array
///
/// # Arguments
/// * array (&[f32]): Array to scan
///
/// # Returns
/// usize: Index of first element with min value
pub fn min_index(array: &[f32]) -> usize
{
    let mut idx: usize = 0;

    for (j, &value) in array.iter().enumerate() {
        if value < array[idx] {
            idx = j;
        }
    }

    idx
}

/// Find optimal size for heating system storage
///
/// # Arguments
/// * pow_t (&f32): Thermal power of heating system in [W]
/// * delta_t (&f32): Temperature spread of heating system in [K]
///                   (difference between standard room temperature [20 degC]
///                    and inlet temperature)
///
/// # Returns
/// f32: Capacity of storage in [Wh]
pub fn find_heating_system_storage(pow_t: &f32, delta_t: &f32) -> f32
{
    let mut diffs: [f32;11] = [0.;11];
    let exact = pow_t * 50.0e-3; // kW * m^3/kW

    for (pos, model) in MODELS.iter().enumerate() {
        diffs[pos] = (exact - model).abs();
    }

    let index = min_index(&diffs);
    let volume = MODELS[index];

    volume * C_WATER * RHO_WATER * delta_t  // in Wh
}

/// Find optimal size for hot water system storage
///
/// The desing is realised according to DIN 4708.
///
/// # Arguments
/// * n (&f32): Characteristic number for buildings hot water demand
/// * delta_t (&f32): Temperature spread of hot system in [K]
///                   (difference between cold water [10 degC]
///                    and hot water temperature [min 60 degC
///                    due hygienic issues])
///
/// # Returns
/// f32: Capacity of storage in [Wh]
pub fn find_hot_water_system_storage(n: &f32, delta_t: &f32) -> f32
{
    // Min. capacity according to DIN
    // 5820. Wh is the energy needed to fill standard bathtub
    let w_2tn = 5820. * n * ((1. + n.sqrt()) / n.sqrt());
    // Volume needed for this capacity
    let min_volume_hw = w_2tn / (delta_t * C_WATER * RHO_WATER);

    // find hot water storage volume
    for model in MODELS.iter() {
        if min_volume_hw < *model {
            return *model * C_WATER * RHO_WATER * delta_t;  // in Wh
        }
    }

    *MODELS.last().unwrap() * C_WATER * RHO_WATER * delta_t  // in Wh
}
