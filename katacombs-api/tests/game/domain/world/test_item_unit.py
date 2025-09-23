import pytest

from src.katacombs.domain.player import Sid
from src.katacombs.domain.world import Action, Item


class TestItem:
    """UNIT TEST: Item Entity Domain Behavior
    Tests the Item entity business logic and validation rules
    """

    def test_item_can_be_created_with_valid_data(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Magic Sword"
        description = "A legendary sword with mystical powers"
        actions = [Action.PICK, Action.USE]

        # Act
        item = Item(item_sid, name, description, actions)

        # Assert
        assert item.sid == item_sid
        assert item.name == name
        assert item.description == description
        assert item.available_actions == actions

    def test_item_can_be_created_without_actions(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Decorative Vase"
        description = "A beautiful but fragile vase"

        # Act
        item = Item(item_sid, name, description)

        # Assert
        assert item.sid == item_sid
        assert item.name == name
        assert item.description == description
        assert item.available_actions == []  # Default empty list

    def test_item_cannot_be_created_with_empty_name(self):
        # Arrange
        item_sid = Sid.generate()
        empty_name = ""
        description = "Some description"

        # Act & Assert
        with pytest.raises(ValueError, match="Item name cannot be empty"):
            Item(item_sid, empty_name, description)

    def test_item_cannot_be_created_with_whitespace_only_name(self):
        # Arrange
        item_sid = Sid.generate()
        whitespace_name = "   \t\n   "
        description = "Some description"

        # Act & Assert
        with pytest.raises(ValueError, match="Item name cannot be empty"):
            Item(item_sid, whitespace_name, description)

    def test_item_cannot_be_created_with_empty_description(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Magic Ring"
        empty_description = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Item description cannot be empty"):
            Item(item_sid, name, empty_description)

    def test_item_cannot_be_created_with_whitespace_only_description(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Magic Ring"
        whitespace_description = "   \t\n   "

        # Act & Assert
        with pytest.raises(ValueError, match="Item description cannot be empty"):
            Item(item_sid, name, whitespace_description)

    def test_item_with_single_action(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Health Potion"
        description = "A potion that restores health when consumed"
        actions = [Action.USE]

        # Act
        item = Item(item_sid, name, description, actions)

        # Assert
        assert item.available_actions == [Action.USE]
        assert Action.USE in item.available_actions
        assert Action.PICK not in item.available_actions

    def test_item_with_multiple_actions(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Torch"
        description = "A burning torch that provides light"
        actions = [Action.PICK, Action.USE]

        # Act
        item = Item(item_sid, name, description, actions)

        # Assert
        assert len(item.available_actions) == 2
        assert Action.PICK in item.available_actions
        assert Action.USE in item.available_actions

    def test_item_actions_can_contain_duplicates(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Strange Artifact"
        description = "An artifact with mysterious properties"
        actions = [Action.USE, Action.USE, Action.PICK]  # Duplicate USE actions

        # Act
        item = Item(item_sid, name, description, actions)

        # Assert
        assert item.available_actions == [Action.USE, Action.USE, Action.PICK]
        assert len(item.available_actions) == 3  # Duplicates preserved

    def test_item_with_valid_name_containing_spaces_and_special_chars(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Ancient Key of Wisdom"
        description = "A key with intricate engravings"

        # Act
        item = Item(item_sid, name, description)

        # Assert
        assert item.name == "Ancient Key of Wisdom"

    def test_item_with_multiline_description(self):
        # Arrange
        item_sid = Sid.generate()
        name = "Spellbook"
        description = "A thick book containing ancient spells.\nIts pages glow with magical energy."

        # Act
        item = Item(item_sid, name, description)

        # Assert
        assert item.description == "A thick book containing ancient spells.\nIts pages glow with magical energy."

    def test_items_are_equal_with_same_sid(self):
        # Arrange
        item_sid = Sid.generate()
        item1 = Item(item_sid, "Sword", "A sharp blade", [Action.PICK])
        item2 = Item(item_sid, "Sword", "A sharp blade", [Action.PICK])

        # Act & Assert
        assert item1 == item2  # Same SID means same item

    def test_items_are_different_with_different_sid(self):
        # Arrange
        item1 = Item(Sid.generate(), "Sword", "A sharp blade", [Action.PICK])
        item2 = Item(Sid.generate(), "Sword", "A sharp blade", [Action.PICK])

        # Act & Assert
        assert item1 != item2  # Different SIDs mean different items