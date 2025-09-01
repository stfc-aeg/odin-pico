import React from 'react';
import './App.css'
import NavigationBar from './components/PicoDashboard/NavigationBar';
import PicoDashboard from './components/PicoDashboard/PicoDashboard';
import { useAdapterEndpoint } from 'odin-react';

function App() {
  const pico_endpoint = useAdapterEndpoint("pico", "http://192.168.0.58:8888", 300);
  const [activeTab, setActiveTab] = React.useState('setup');

  return (
    <>
      <NavigationBar pico_endpoint={pico_endpoint} activeTab={activeTab} setActiveTab={setActiveTab} />
      <PicoDashboard pico_endpoint={pico_endpoint} activeTab={activeTab} />
    </>
  )
}

export default App
