import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Navbar from '@/components/Navbar'

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), refresh: jest.fn() }),
  usePathname: () => '/',
}))

jest.mock('@/components/AuthProvider', () => ({
  useAuth: () => ({
    isAuthenticated: false,
    user: null,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}))

jest.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}))

describe('Navbar', () => {
  it('renders the logo and Rework text', () => {
    render(<Navbar />)
    
    expect(screen.getByText('Rework')).toBeInTheDocument()
    expect(screen.getByText('Cognitive Workspace')).toBeInTheDocument()
  })
  
  it('shows Login and Register when unauthenticated', () => {
    render(<Navbar />)
    
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByText('Register')).toBeInTheDocument()
  })
})
