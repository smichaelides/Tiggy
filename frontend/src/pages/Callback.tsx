import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function Callback() {
  // TODO: implement proper authentication and renavigate to homepage.
  const navigate = useNavigate();

  useEffect(() => {
    navigate("/");
  }, [navigate]);

  return <div>Loading...</div>;
}

export default Callback;
