# FIFA World Cup 2026 — Team Statistics Glossary

Definitions for the metrics found in the `team_stats_*.csv` files, grouped by tab.

## Attacking

| Metric | Description |
| --- | --- |
| Goals | Total occasions a player or team successfully places the ball into the opponent's net. |
| Assists | A player who last touches the ball before a teammate scores, regardless of intention, subject to FIFA's assist rules. |
| Attempts At Goal | Total number of shots taken, including on-target, off-target, blocked, and saved attempts. |
| Attempts On Target | Shots that end within the goal frame, including goals and saves. |
| Attempt At Goal Conv. Rate (%) | Percentage of total shots that result in goals. |
| xG | Expected Goals. A model estimating the probability that a shot results in a goal based on factors such as location, shot type, assist type, and defensive pressure. |
| xG Efficiency (%) | Goals divided by Expected Goals (xG), measuring finishing efficiency relative to chance quality. |
| Corners | Corner kicks awarded when the defending team last touches the ball before it crosses its own goal line. |
| Possession Control | Percentage of time a team controls possession, including a separate contested state when neither team controls the ball. |

## Distribution

| Metric | Description |
| --- | --- |
| Passes | Deliberate transfers of the ball between teammates. |
| Passing Accuracy | Percentage of attempted passes successfully completed. |
| Crosses | Balls delivered from wide areas towards the opponent's penalty area. |
| Crossing Accuracy | Percentage of crosses successfully reaching the intended teammate. |
| Defensive Linebreaks Attempted | Distributions or actions attempting to penetrate the opposition's defensive line. |
| Defensive Linebreaks Acc (%) | Percentage of attempted defensive linebreaks completed successfully. |
| Switches of Play Completed | Successful switches of play reaching a teammate on the opposite side of the pitch while bypassing at least two vertical channels. |
| Switches of Play Acc (%) | Percentage of attempted switches of play completed successfully. |

## Defending

| Metric | Description |
| --- | --- |
| Goals Conceded | Total number of goals allowed by a team. |
| Own Goals | Goals scored accidentally into a player's own net. |
| Forced Turnovers | Situations where pressure, tackles, or interceptions force the opposition to lose possession. |
| Ball Recovery Time | Time taken for a team to regain possession after losing it. |
| Defensive Pressures Applied | Total pressing actions used to challenge possession and disrupt the opponent. |
| Defensive Pressures Directly Applied | Pressures specifically applied to the player currently in possession of the ball. |

## Discipline

| Metric | Description |
| --- | --- |
| Fouls Against | Number of fouls committed by a player or team. |
| Fouls For | Number of fouls won by a player or team. |
| Yellow Cards | Official cautions issued by the referee. |
| Red Cards | Direct dismissals resulting in a player being sent off. |
| Indirect Red Cards | Dismissals resulting from two yellow cards in the same match. |
| Offsides | Instances where a player is penalized for being offside while actively involved in play. |

## Goalkeeping

| Metric | Description |
| --- | --- |
| Clean Sheets | Matches in which a team concedes no goals. |
| Goalkeeper Goal Preventions | Successful goalkeeping actions that prevent goals, including saves and deflections. |
| Goalkeeper Actions Inside the Penalty Area | Goalkeeper interventions inside their own penalty area, including saves, claims, and punches. |
| Goalkeeper Actions Outside the Penalty Area | Goalkeeper interventions outside the penalty area, such as clearances and tackles. |

## Movement

| Metric | Description |
| --- | --- |
| Offers To Receive | When a player actively signals, changes body shape, or makes a clear movement to receive the ball from a teammate. |
| Offers In Behind | When a player actively signals, changes body shape, or makes a clear movement to receive the ball behind the opposition's defensive line. |
| Offers In Between | When a player actively signals, changes body shape, or makes a clear movement to receive the ball between the opposition's team shape or units. |
| Offers In Front | When a player actively signals, changes body shape, or makes a clear movement to receive the ball in front of the opposition's team shape. |
| Offers Inside Team Shape | When a player actively signals, changes body shape, or makes a clear movement to receive the ball inside the opposition's team shape. |
| Offers Outside Team Shape | When a player actively signals, changes body shape, or makes a clear movement to receive the ball outside the opposition's team shape. |
| Receptions In Behind | Successful receptions of the ball beyond the opposition's last defensive line, indicating threat creation. |
| Receptions Between Midfield And Defensive Line | Receptions of the ball in the space between the opposition's midfield and defensive line, facilitating vertical progression towards goal. |
| Receptions Under Pressure | Instances where a player receives the ball while being actively pressed or challenged by an opponent. |

## Physical

| Metric | Description |
| --- | --- |
| Average Speed (km/h) | Average running speed maintained throughout the match. |
| Top Speed (km/h) | Maximum speed reached during the match. |
| High Speed Running | Runs performed above a predefined high-speed threshold. |
| Sprints | Explosive runs above a predefined sprint-speed threshold. |
| Total Distance (km) | Total distance covered during the match across all movement intensities. |
