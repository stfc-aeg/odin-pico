import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { OdinErrorContext } from 'odin-react'
import 'bootstrap/dist/css/bootstrap.min.css';


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <OdinErrorContext>
      <App />
    </OdinErrorContext>
  </StrictMode>,
)
