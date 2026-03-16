import "../styles/about.css";

export default function About() {
  return (
    <div className="about-container">

      <div className="about-card">
        <h1>About CacheMeOutside</h1>

        <p>
          CacheMeOutside is a cybersecurity research project focused on improving
          authentication through behavioral analysis. Instead of relying solely on
          traditional CAPTCHA or passwords, the system analyzes how users interact
          with a login screen to determine whether a login attempt is human or automated.
        </p>

        <p>
          Behavioral signals such as typing rhythm, mouse movement, and interaction
          timing are collected and analyzed by machine learning models. These signals
          help the system distinguish real users from bots without introducing extra
          friction into the login experience.
        </p>

        <p>
          The goal is to create a smarter authentication process that improves security
          while remaining seamless for legitimate users.
        </p>
      </div>


      <div className="about-card">
        <h2>Team CacheMeOutside</h2>

        <ul className="team-list">
          <li><strong>Andrew Klusmeyer</strong> — Data Team (Information Security)</li>
          <li><strong>Sophie Blick</strong> — Front-End Team</li>
          <li><strong>Ming Lin</strong> — Front-End Team</li>
          <li><strong>Pari Patel</strong> — Data Team</li>
          <li><strong>Rohitha Sresta</strong> — Data Team</li>
          <li><strong>Nolan Park</strong> — Model Team (Machine Learning)</li>
        </ul>
      </div>


      <div className="about-card">
        <h2>Project Mentor</h2>
        <p>
          Professor Ekincan Ufuktepe — Research mentor specializing in artificial
          intelligence and cybersecurity systems.
        </p>
      </div>

    </div>
  );
}