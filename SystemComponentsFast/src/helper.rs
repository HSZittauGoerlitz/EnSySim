/// Find first occurrence of min value in given float array
///
/// # Arguments
/// * array (&[f32]): Array to scan
///
/// # Returns
/// usize: Index of first element with min value
pub fn min_index(array: &[f32]) -> usize {
    let mut idx: usize = 0;

    for (j, &value) in array.iter().enumerate() {
        if value < array[idx] {
            idx = j;
        }
    }

    idx
}