// external
use pyo3::prelude::*;
use std::collections::VecDeque;

#[pyclass]
#[derive(Clone)]
pub struct HistMemory {
    pub memory: VecDeque<f32>,
    pub size: usize,
}

#[pymethods]
impl HistMemory {
    pub fn get_memory(&self) -> Vec<f32>{
        Vec::from(self.memory.clone())
    }
}

impl HistMemory {
    /// Create manager for history memory
    pub fn new(size: usize) -> Self {
        HistMemory {memory: VecDeque::with_capacity(size),
                    size: size
                    }
    }

    /// Remove all elements from memory
    pub fn clear(&mut self) {
        self.memory.clear();
    }

    /// Change size of memory and keep saved values
    /// (if they fit into new size)
    ///
    /// # Arguments
    /// * size (usize): New memory size
    pub fn resize(&mut self, size: usize) {
        let old_len = self.size;
        self.size = size;
        let old_memory = self.memory.clone();
        self.memory = VecDeque::with_capacity(size);

        let len;
        if old_len < size {
            len = old_len;
        } else {
            len = size;
        }

        for idx in 0..len {
            self.memory.push_back(old_memory[idx]);
        }
    }

    pub fn save(&mut self, value: f32) {
        if self.memory.len() < self.size {
            self.memory.push_back(value);
        } else {
            // remove first, that capacity is not exceeded
            self.memory.pop_front();
            self.memory.push_back(value);
        }
    }
}

// saving -> avoid reimplementation for different types
#[macro_export]
macro_rules! save_e {
    ($self:expr, $e_gen:expr, $e_load:expr) => {
        match &mut $self.gen_e {
            None => {},
            Some(gen_e) => {
                 gen_e.save($e_gen)
            },
        }
        match &mut $self.load_e {
            None => {},
            Some(load_e) => {
                 load_e.save($e_load)
            },
        }
    }
}

#[macro_export]
macro_rules! save_t {
    ($self:expr, $t_gen:expr, $t_load:expr) => {
        match &mut $self.gen_t {
            None => {},
            Some(gen_t) => {
                 gen_t.save($t_gen)
            },
        }
        match &mut $self.load_t {
            None => {},
            Some(load_t) => {
                 load_t.save($t_load)
            },
        }
    }
}
