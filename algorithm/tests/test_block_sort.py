import unittest

from algorithm.block_sort import sort_blocks

class TestSortBlocks(unittest.TestCase):

    def test_arreglo_vacio(self):
        self.assertEqual(sort_blocks([]), "X")

    def test_un_solo_cero(self):
        self.assertEqual(sort_blocks([0]), "X X")

    def test_solo_ceros(self):
        self.assertEqual(sort_blocks([0, 0, 0]), "X X X X")

    def test_cero_al_inicio(self):
        self.assertEqual(sort_blocks([0, 1, 2, 3]), "X 123")

    def test_cero_al_final(self):
        self.assertEqual(sort_blocks([1, 2, 3, 0]), "123 X")

    def test_sin_ceros(self):
        self.assertEqual(sort_blocks([3, 1, 2]), "123")

    def test_un_solo_numero(self):
        self.assertEqual(sort_blocks([5]), "5")

    def test_ejemplo_enunciado(self):
        self.assertEqual(
            sort_blocks([1, 3, 2, 0, 7, 8, 1, 3, 0, 6, 7, 1]),
            "123 1378 167"
        )

    def test_bloques_consecutivos_vacios(self):
        self.assertEqual(
            sort_blocks([2, 1, 0, 0, 3, 4]),
            "12 X 34"
        )
    


if __name__ == "__main__":
    unittest.main()