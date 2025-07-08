import React from 'react';
import './App.css'
import Component from './components/Component';
import NavigationBar from './components/PicoDashboard/NavigationBar';
import PicoDashboard from './components/PicoDashboard/PicoDashboard';
import { useAdapterEndpoint } from 'odin-react';

function App() {
  const pico_endpoint = useAdapterEndpoint("pico", "http://192.168.0.28:8888", 300);

  React.useEffect(() => {
      pico_endpoint.refreshData();
  }, []);

  return (
    <>
      <NavigationBar pico_endpoint={pico_endpoint} />
      <PicoDashboard pico_endpoint={pico_endpoint} />
    </>
  )
}

export default App
