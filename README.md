# HSNU Game System

A web-based character card management system built with Flask for tabletop RPG games.

## Features

- **Character Management**: Create and manage player characters with stats and items
- **Password Protection**: Each character is protected with individual passwords
- **Admin Panel**: Complete administrative interface for game masters
- **Item Templates**: Reusable item templates for easy inventory management
- **Bulk Operations**: Add stats or items to multiple characters at once
- **Responsive Design**: Works seamlessly on both desktop and mobile devices
- **Search Functionality**: Quick search through character names and descriptions

## Quick Start

1. Install dependencies:

   ```bash
   pip install flask flask-sqlalchemy werkzeug
   ```

2. Run the application:

   ```bash
   python app.py
   ```

3. Access the system at `http://localhost:5001`

4. Default admin password: `ykhzYhQVXzFOvXn`

## Project Structure

```text
├── app.py              # Main application file
├── config.py           # Configuration settings
├── models.py           # Database models
├── routes/             # Route handlers
│   ├── main.py         # Public routes
│   └── admin.py        # Admin routes
├── templates/          # HTML templates
├── static/             # Static files (CSS, images)
└── uploads/            # File uploads
```

## Usage

### For Players

- Browse available characters on the homepage
- Enter character password to view detailed stats and inventory
- Use search to quickly find specific characters

### For Administrators

- Access admin panel to create and manage characters
- Set up item templates for consistent inventory management
- Use bulk operations to update multiple characters simultaneously
- Configure system settings and backgrounds

## Database

The system uses SQLite database with the following main models:

- `Player`: Character information and credentials
- `Stat`: Character statistics (health, mana, etc.)
- `Item`: Character inventory items
- `ItemTemplate`: Reusable item templates
- `SiteConfig`: System configuration

## License

This project is open source and available under the MIT License.
