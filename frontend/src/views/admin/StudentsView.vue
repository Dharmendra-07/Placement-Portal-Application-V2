<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Manage Students</h5>

    <div class="row g-2 mb-3 align-items-end">
      <div class="col-md-4">
        <label class="form-label small fw-medium">Search</label>
        <input v-model="filters.q" type="text" class="form-control"
               placeholder="Name, roll number, email, phone..." @input="fetchStudents" />
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Department</label>
        <input v-model="filters.department" type="text" class="form-control"
               placeholder="CSE, ECE..." @input="fetchStudents" />
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Year</label>
        <select v-model="filters.year" class="form-select" @change="fetchStudents">
          <option value="">All years</option>
          <option v-for="y in [1,2,3,4]" :key="y" :value="y">Year {{ y }}</option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-medium">Status</label>
        <select v-model="filters.blacklisted" class="form-select" @change="fetchStudents">
          <option value="">All</option>
          <option value="true">Blacklisted only</option>
        </select>
      </div>
      <div class="col-md-2">
        <button class="btn btn-outline-secondary w-100" @click="resetFilters">Reset</button>
      </div>
    </div>

    <div class="text-muted small mb-2">{{ pagination.total }} students found</div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="students.length === 0" class="text-muted text-center py-5">
      No students found.
    </div>
    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th>#</th>
              <th>Student</th>
              <th>Roll No.</th>
              <th>Dept / Year</th>
              <th>CGPA</th>
              <th>Skills</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in students" :key="s.id">
              <td class="text-muted small">{{ s.id }}</td>
              <td>
                <div class="fw-medium">{{ s.full_name }}</div>
                <div class="text-muted small">{{ s.email }}</div>
              </td>
              <td class="small">{{ s.roll_number || '—' }}</td>
              <td class="small">{{ s.department || '—' }} / Yr {{ s.year || '?' }}</td>
              <td class="small fw-medium">{{ s.cgpa || '—' }}</td>
              <td class="small text-muted" style="max-width:160px">
                <span class="text-truncate d-block">{{ s.skills || '—' }}</span>
              </td>
              <td>
                <span v-if="s.is_blacklisted"  class="badge bg-dark">Blacklisted</span>
                <span v-else-if="!s.is_active" class="badge bg-secondary">Inactive</span>
                <span v-else                   class="badge bg-success">Active</span>
              </td>
              <td>
                <div class="d-flex gap-1">
                  <button v-if="!s.is_blacklisted"
                          class="btn btn-sm btn-outline-danger"
                          @click="blacklist(s.id)">Blacklist</button>
                  <button v-else
                          class="btn btn-sm btn-outline-success"
                          @click="activate(s.id)">Restore</button>
                  <button class="btn btn-sm btn-outline-secondary"
                          @click="remove(s.id)">Remove</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <nav v-if="pagination.pages > 1">
        <ul class="pagination pagination-sm justify-content-center">
          <li class="page-item" :class="{ disabled: pagination.page === 1 }">
            <button class="page-link" @click="changePage(pagination.page - 1)">‹</button>
          </li>
          <li v-for="p in pagination.pages" :key="p"
              class="page-item" :class="{ active: p === pagination.page }">
            <button class="page-link" @click="changePage(p)">{{ p }}</button>
          </li>
          <li class="page-item" :class="{ disabled: pagination.page === pagination.pages }">
            <button class="page-link" @click="changePage(pagination.page + 1)">›</button>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'AdminStudentsView',
  data() {
    return {
      students: [], loading: true,
      filters: { q: '', department: '', year: '', blacklisted: '' },
      pagination: { page: 1, pages: 1, total: 0 },
    }
  },
  created() { this.fetchStudents() },
  methods: {
    async fetchStudents(page = 1) {
      this.loading = true
      try {
        const { data } = await api.get('/admin/students', {
          params: { ...this.filters, page }
        })
        this.students   = data.students
        this.pagination = { page: data.page, pages: data.pages, total: data.total }
      } finally { this.loading = false }
    },
    changePage(p) { if (p >= 1 && p <= this.pagination.pages) this.fetchStudents(p) },
    resetFilters() { this.filters = { q: '', department: '', year: '', blacklisted: '' }; this.fetchStudents() },
    async blacklist(id) {
      if (!confirm('Blacklist this student?')) return
      await api.put(`/admin/students/${id}/blacklist`); this.fetchStudents()
    },
    async activate(id) { await api.put(`/admin/students/${id}/activate`); this.fetchStudents() },
    async remove(id) {
      if (!confirm('Permanently remove this student?')) return
      await api.delete(`/admin/students/${id}`); this.fetchStudents()
    },
  },
}
</script>
