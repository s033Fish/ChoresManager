import React from 'react';

const positions = [
    { name: 'GK', top: '85%', left: '50%', positionType: 'Goalkeeper' },
    { name: 'DEF1', top: '65%', left: '20%', positionType: 'Defender' },
    { name: 'DEF2', top: '65%', left: '40%', positionType: 'Defender' },
    { name: 'DEF3', top: '65%', left: '60%', positionType: 'Defender' },
    { name: 'DEF4', top: '65%', left: '80%', positionType: 'Defender' },
    { name: 'MID1', top: '40%', left: '25%', positionType: 'Midfielder' },
    { name: 'MID2', top: '40%', left: '50%', positionType: 'Midfielder' },
    { name: 'MID3', top: '40%', left: '75%', positionType: 'Midfielder' },
    { name: 'FWD1', top: '15%', left: '25%', positionType: 'Attacker' },
    { name: 'FWD2', top: '15%', left: '50%', positionType: 'Attacker' },
    { name: 'FWD3', top: '15%', left: '75%', positionType: 'Attacker' },
];

const Field = ({ selectedPlayers, selectPosition, removePlayer }) => {
  return (
    <div className="field">
      {positions.map((pos) => (
        <div
          key={pos.name}
          className="position"
          style={{ top: pos.top, left: pos.left }}
          onClick={() => selectPosition(pos)}
        >
          {selectedPlayers[pos.name] ? (
            <div className="player-card">
              <button
                className="remove-player-button"
                onClick={(e) => {
                  e.stopPropagation();
                  removePlayer(pos.name);
                }}
              >
                ✕
              </button>
              <div className="card-header">
                <img
                  className="team-logo"
                  src={`../static/img/${selectedPlayers[pos.name].team.toLowerCase().replace(/\s+/g, '_')}.png`}
                  alt={`${selectedPlayers[pos.name].team} logo`}
                />
              </div>
              <div className="card-content">
                <div className="player-name">
                  {selectedPlayers[pos.name].name}
                </div>
                <div className="player-price">
                  Price: ${selectedPlayers[pos.name].price}
                </div>
              </div>
            </div>
          ) : (
            <div className="placeholder">Select {pos.name}</div>
          )}
        </div>
      ))}
    </div>
  );
};

export default Field;