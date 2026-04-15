import { createStore } from 'vuex'

const TOKEN_KEY = 'yunnan_token'
const USER_KEY = 'yunnan_user'

export default createStore({
  state: {
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  },
  getters: {
    isAuthenticated: state => !!state.token,
    userRole: state => state.user?.role || '',
    userName: state => state.user?.full_name || state.user?.username || '',
    isAdmin: state => state.user?.role === 'admin',
  },
  mutations: {
    SET_AUTH(state, { token, user }) {
      state.token = token
      state.user = user
      localStorage.setItem(TOKEN_KEY, token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    CLEAR_AUTH(state) {
      state.token = null
      state.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
  actions: {
    login({ commit }, payload) {
      commit('SET_AUTH', payload)
    },
    logout({ commit }) {
      commit('CLEAR_AUTH')
    },
  }
})
