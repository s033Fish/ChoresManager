import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import PlayerList from './components/Playerlist';
import Field from './components/Field';
import '../Players.css';

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const App = () => {
  const [players, setPlayers] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState({});
  const [selectedPosition, setSelectedPosition] = useState(null);
  const [captain, setCaptain] = useState(null);
  const [isLineupComplete, setIsLineupComplete] = useState(false);
  const [budget, setBudget] = useState(1200.00);
  const [totalPoints, setTotalPoints] = useState(0);

  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        console.log("Fetching players...");
        const response = await fetch('/api/players/');
        if (!response.ok) throw new Error('Failed to fetch players');
        
        const data = await response.json();
        console.log("Data fetched from API:", data);
  
        setPlayers(data.players);
        console.log("Players state after setPlayers:", data.players);
      } catch (error) {
        console.error("Error fetching players:", error);
        alert("Failed to load players. Please try again.");
      }
    };

    const fetchSelectedPlayers = async () => {
      try {
        console.log("Fetching selected players...");
        const response = await fetch('/api/selected-players/');
        if (!response.ok) throw new Error('Failed to fetch selected players');
        
        const data = await response.json();
        console.log("Data fetched for selected players:", data);

        if (data.selectedPlayers) {
          const loadedSelectedPlayers = {};

          // Make sure to correctly assign each player to their correct position key
          Object.keys(data.selectedPlayers).forEach((key) => {
            const player = data.selectedPlayers[key];
            if (player.position === "Goalkeeper") {
              loadedSelectedPlayers["GK"] = player;
            } else if (player.position === "Defender") {
              // Distribute defenders into DEF1, DEF2, DEF3, DEF4
              const numDefenders = Object.keys(loadedSelectedPlayers).filter(k => k.startsWith('DEF')).length + 1;
              loadedSelectedPlayers[`DEF${numDefenders}`] = player;
            } else if (player.position === "Midfielder") {
              // Distribute midfielders into MID1, MID2, MID3
              const numMidfielders = Object.keys(loadedSelectedPlayers).filter(k => k.startsWith('MID')).length + 1;
              loadedSelectedPlayers[`MID${numMidfielders}`] = player;
            } else if (player.position === "Attacker") {
              // Distribute attackers into FWD1, FWD2, FWD3
              const numForwards = Object.keys(loadedSelectedPlayers).filter(k => k.startsWith('FWD')).length + 1;
              loadedSelectedPlayers[`FWD${numForwards}`] = player;
            }
          });

          setSelectedPlayers(loadedSelectedPlayers);

          // Update budget
          const totalSelectedPrice = Object.values(loadedSelectedPlayers).reduce((acc, player) => acc + parseFloat(player.price), 0);
          setBudget(1200.00 - totalSelectedPrice);

          // Update total points
          const calculatedTotalPoints = Object.values(loadedSelectedPlayers).reduce((acc, player) => acc + player.past_points, 0);
          setTotalPoints(calculatedTotalPoints);

          // Set captain if available
          if (data.captain) {
            setCaptain(data.captain);
          }

          // Set lineup complete status
          if (Object.keys(loadedSelectedPlayers).length === 11) {
            setIsLineupComplete(true);
          }
        }
      } catch (error) {
        console.error("Error fetching selected players:", error);
      }
    };

    fetchPlayers();
    fetchSelectedPlayers();
  }, []);

  const availablePlayers = players.filter(
    player => !Object.values(selectedPlayers).some(selectedPlayer => selectedPlayer.id === player.id)
  );
  console.log("Available Players:", availablePlayers);

  const handleSelectPosition = (position) => {
    setSelectedPosition(position);
  };

  const handleSelectPlayer = (player) => {
    if (selectedPosition && player.position === selectedPosition.positionType) {
      if (player.price > budget) {
        alert(`You don't have enough budget to select this player. Remaining budget: $${budget}`);
        return;
      }

      const updatedPlayers = { ...selectedPlayers, [selectedPosition.name]: player };
      setSelectedPlayers(updatedPlayers);
      setSelectedPosition(null);

      // Update budget
      setBudget((prevBudget) => {
        const updatedBudget = parseFloat(prevBudget) - player.price;
        console.log(`Budget after selecting player: ${updatedBudget}`);
        return updatedBudget;
      });

      // Update total points
      setTotalPoints((prevTotalPoints) => prevTotalPoints + player.past_points);

      if (Object.keys(updatedPlayers).length === 11) {
        setIsLineupComplete(true);
      }
    } else {
      alert(`Select a player with position: ${selectedPosition.positionType}`);
    }
  };

  const handleRemovePlayer = (positionName) => {
    if (selectedPlayers[positionName]) {
      const playerPrice = selectedPlayers[positionName].price;
      const playerPoints = selectedPlayers[positionName].past_points;
      const updatedPlayers = { ...selectedPlayers };
      delete updatedPlayers[positionName];

      setSelectedPlayers(updatedPlayers);

      // Update budget
      setBudget((prevBudget) => {
        const updatedBudget = parseFloat(prevBudget) + parseFloat(playerPrice);
        console.log(`Budget after removing player: ${updatedBudget}`);
        return updatedBudget;
      });

      // Update total points
      setTotalPoints((prevTotalPoints) => prevTotalPoints - playerPoints);

      setIsLineupComplete(Object.keys(updatedPlayers).length === 11);
    }
  };

  const handleCaptainSelection = (event) => {
    const selectedPlayerId = parseInt(event.target.value);
    const selectedCaptain = Object.values(selectedPlayers).find(player => player.id === selectedPlayerId);
    setCaptain(selectedCaptain);
  };

  const handleSubmitLineup = async () => {
    if (isLineupComplete && captain) {
      try {
        const response = await fetch('/select-lineup/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: JSON.stringify({
            players: Object.values(selectedPlayers).map(player => player.id),
            captain_id: captain.id,
          }),
        });

        const result = await response.json();
        if (response.ok) {
          alert(result.message);

          setCaptain(null);
          setIsLineupComplete(false);
          setSelectedPosition(null);
          setBudget(1300);
          setTotalPoints(0);
        } else {
          alert(result.error || 'Failed to save lineup');
        }
      } catch (error) {
        console.error("Error submitting lineup:", error);
        alert("There was an error submitting your lineup.");
      }
    } else {
      alert("Please select all 11 players and choose a captain.");
    }
  };

  return (
    <div className="app">
      <div className="info-display">
        <h3>Remaining Budget: ${Math.round(budget * 100) / 100}</h3>
      </div>
      <div className="main-content-row">
        <Field
          selectedPlayers={selectedPlayers}
          selectPosition={handleSelectPosition}
          removePlayer={handleRemovePlayer}
        />
        <PlayerList
          players={availablePlayers}
          selectPlayer={handleSelectPlayer}
          selectedPosition={selectedPosition}
        />
      </div>
  
      {isLineupComplete && (
        <div>
          <div>
            <div>
              <h3>Select Your Captain:</h3>
              <select onChange={handleCaptainSelection} value={captain ? captain.id : ''}>
                <option value="" disabled>Select a captain</option>
                {Object.values(selectedPlayers).map(player => (
                  <option key={player.id} value={player.id}>
                    {player.name} ({player.team})
                  </option>
                ))}
              </select>
            </div>
    
            <div>
              <button onClick={handleSubmitLineup} disabled={!isLineupComplete || !captain}>
                Submit Lineup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const root = createRoot(document.getElementById('root'));
root.render(<App />);
