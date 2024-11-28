import React, { useState } from 'react';

const PlayerList = ({ players, selectPlayer, selectedPosition }) => {
  const [sortCriteria, setSortCriteria] = useState('price');

  console.log("Rendering PlayerList with players:", players);
  console.log("Selected Position:", selectedPosition);

  let filteredPlayers = [];

  if (selectedPosition) {
    console.log("Filtering players for position:", selectedPosition.positionType);
    filteredPlayers = players.filter(
      (player) => player.position === selectedPosition.positionType
    );
    filteredPlayers.sort((a, b) => b.past_points - a.past_points);
  }

  return (
    <div className="player-list">
      <h3>Available Players</h3>
      {selectedPosition ? (
        <>
          {filteredPlayers.length > 0 ? (
            <table className="player-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Team</th>
                  <th>Position</th>
                  <th>Price</th>
                  <th>Total Points</th>
                  <th>Select</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.map((player) => (
                  <tr key={player.id}>
                    <td>{player.name}</td>
                    <td>{player.team}</td>
                    <td>{player.position}</td>
                    <td>${player.price}</td>
                    <td>{player.past_points}</td>
                    <td>
                      <button
                        className="select-player-button"
                        onClick={() => selectPlayer(player)}
                      >
                        Select
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No players available for the selected position.</p>
          )}
        </>
      ) : (
        <p>Select a position on the field</p>
      )}
    </div>
  );
};

export default PlayerList;
