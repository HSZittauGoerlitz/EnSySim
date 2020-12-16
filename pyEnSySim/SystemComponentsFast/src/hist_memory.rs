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