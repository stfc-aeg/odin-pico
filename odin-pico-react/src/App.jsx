import React from 'react';
import './App.css'
import NavigationBar from './components/PicoDashboard/NavigationBar';
import PicoDashboard from './components/PicoDashboard/PicoDashboard';
import { useAdapterEndpoint } from 'odin-react';

function App() {
  const url = import.meta.env.VITE_ENDPOINT_URL;
  const pico_endpoint = useAdapterEndpoint("pico", url, 300);
  const [activeTab, setActiveTab] = React.useState('setup');

  // let gpio_endpoint = null

  // pico_endpoint.get('device/gpio/enabled')
  //   .then((response) => {
  //     if (response.enabled == true) {
  //       gpio_endpoint = useAdapterEndpoint("triggering", url, 300);
  //     }
  //   });

  const gpio_endpoint = useAdapterEndpoint("triggering", url, 300);

  return (
    <>
      <NavigationBar pico_endpoint={pico_endpoint} activeTab={activeTab} setActiveTab={setActiveTab} />
      <PicoDashboard pico_endpoint={pico_endpoint} gpio_endpoint={gpio_endpoint} activeTab={activeTab} />
    </>
  )
}

export default App
