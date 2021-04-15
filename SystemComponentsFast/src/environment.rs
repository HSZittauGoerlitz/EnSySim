// external
use pyo3::prelude::*;

#[pyclass]
#[derive(Clone)]
pub struct Environment {
    #[pyo3(get)]
    pub irradiation_dir: f32,
    pub irradiation_diff: f32,
    pub irradiation_all: f32,
    pub t_out: f32,
}

#[pymethods]
impl Environment {

    /// * hist (usize): Size of history memory (0 for no memory)
    #[new]
    pub fn new(direct: f32, diffuse: f32, t_out: f32) -> Self {

        let irradiation_dir = direct;
        let irradiation_diff = diffuse;
        let irradiation_all = irradiation_dir + irradiation_diff;


        let environment = Environment {irradiation_dir: irradiation_dir,
                                       irradiation_diff: irradiation_diff,
                                       irradiation_all : irradiation_all,
                                       t_out: t_out
                    };
        environment
    }
}

impl Environment {}