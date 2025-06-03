-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 12-03-2025 a las 09:40:47
-- Versión del servidor: 10.4.28-MariaDB
-- Versión de PHP: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `chatbot_prueba`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categorias`
--

CREATE TABLE `categorias` (
  `id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

--
-- Volcado de datos para la tabla `categorias`
--

INSERT INTO `categorias` (`id`, `nombre`) VALUES
(1, 'Productos y Servicios'),
(2, 'Campañas de Marketing'),
(3, 'Soporte Técnico'),
(4, 'Preguntas Frecuentes'),
(5, 'Contacto y Ubicación'),
(6, 'Promociones y Ofertas'),
(7, 'Política de Devoluciones'),
(8, 'Nuestro Equipo'),
(9, 'Sostenibilidad');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `conversaciones`
--

CREATE TABLE `conversaciones` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `consulta` text NOT NULL,
  `respuesta` text NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `palabras_clave`
--

CREATE TABLE `palabras_clave` (
  `id` int(11) NOT NULL,
  `subcategoria_id` int(11) DEFAULT NULL,
  `palabra` varchar(255) NOT NULL,
  `peso` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

--
-- Volcado de datos para la tabla `palabras_clave`
--

INSERT INTO `palabras_clave` (`id`, `subcategoria_id`, `palabra`, `peso`) VALUES
(1, 1, 'software', NULL),
(2, 1, 'desarrollo', NULL),
(3, 1, 'personalizado', NULL),
(4, 1, 'medida', NULL),
(5, 2, 'consultoría', NULL),
(6, 2, 'transformación', NULL),
(7, 2, 'digital', NULL),
(8, 2, 'negocio', NULL),
(9, 3, 'soluciones', NULL),
(10, 3, 'nube', NULL),
(11, 3, 'almacenamiento', NULL),
(12, 3, 'datos', NULL),
(13, 4, 'ciberseguridad', NULL),
(14, 4, 'protección', NULL),
(15, 4, 'amenazas', NULL),
(16, 4, 'cibernéticas', NULL),
(17, 5, 'campañas', NULL),
(18, 5, 'IA', NULL),
(19, 5, 'inteligencia', NULL),
(20, 5, 'artificial', NULL),
(21, 6, 'soporte', NULL),
(22, 6, 'técnico', NULL),
(23, 6, '24/7', NULL),
(24, 6, 'incidencias', NULL),
(25, 7, 'preguntas', NULL),
(26, 7, 'frecuentes', NULL),
(27, 7, 'desarrollo', NULL),
(28, 7, 'apps', NULL),
(29, 8, 'contacto', NULL),
(30, 8, 'ubicación', NULL),
(31, 8, 'oficina', NULL),
(32, 8, 'madrid', NULL),
(33, 9, 'promociones', NULL),
(34, 9, 'ofertas', NULL),
(35, 9, 'descuento', NULL),
(36, 9, 'consultoría', NULL),
(37, 10, 'política', NULL),
(38, 10, 'devoluciones', NULL),
(39, 10, 'reembolso', NULL),
(40, 10, '30', NULL),
(41, 10, 'días', NULL),
(42, 11, 'equipo', NULL),
(43, 11, 'expertos', NULL),
(44, 11, 'tecnología', NULL),
(45, 11, 'ingenieros', NULL),
(46, 12, 'sostenibilidad', NULL),
(47, 12, 'prácticas', NULL),
(48, 12, 'ecológicas', NULL),
(49, 12, 'operaciones', NULL),
(50, 13, 'Videojuegos', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `subcategorias`
--

CREATE TABLE `subcategorias` (
  `id` int(11) NOT NULL,
  `categoria_id` int(11) DEFAULT NULL,
  `nombre` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `preguntas_frecuentes` text DEFAULT NULL,
  `ejemplos_uso` text DEFAULT NULL,
  `enlace_recursos` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

--
-- Volcado de datos para la tabla `subcategorias`
--

INSERT INTO `subcategorias` (`id`, `categoria_id`, `nombre`, `descripcion`, `preguntas_frecuentes`, `ejemplos_uso`, `enlace_recursos`) VALUES
(1, 1, 'Desarrollo de Software a Medida', 'Soluciones de software personalizadas para tus necesidades.', NULL, NULL, NULL),
(2, 1, 'Consultoría en Transformación Digital', 'Asesoramiento experto para la digitalización de tu negocio.', NULL, NULL, NULL),
(3, 1, 'Soluciones en la Nube', 'Servicios de almacenamiento y gestión de datos en la nube.', NULL, NULL, NULL),
(4, 1, 'Ciberseguridad Avanzada', 'Protección integral contra amenazas cibernéticas.', NULL, NULL, NULL),
(5, 2, 'Campañas de IA', 'Campañas centradas en soluciones de inteligencia artificial.', NULL, NULL, NULL),
(6, 3, 'Soporte 24/7', 'Soporte técnico disponible 24/7.', NULL, NULL, NULL),
(7, 4, 'Desarrollo de Apps', 'Información sobre el desarrollo de aplicaciones móviles.', NULL, NULL, NULL),
(8, 5, 'Oficina Madrid', 'Nuestra oficina principal se encuentra en Madrid.', NULL, NULL, NULL),
(9, 6, 'Descuento Consultoría', '20% de descuento en servicios de consultoría.', NULL, NULL, NULL),
(10, 7, 'Reembolso 30 días', 'Garantía de reembolso del 100% dentro de los 30 días.', NULL, NULL, NULL),
(11, 8, 'Expertos en Tecnología', 'Contamos con un equipo de expertos en tecnología.', NULL, NULL, NULL),
(12, 9, 'Prácticas Ecológicas', 'Implementamos prácticas ecológicas en nuestras operaciones.', NULL, NULL, NULL),
(13, 1, 'Videojuegos', 'Los videojuegos son experiencias interactivas que combinan arte, tecnología y narrativa.', NULL, NULL, NULL);

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `categorias`
--
ALTER TABLE `categorias`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `conversaciones`
--
ALTER TABLE `conversaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `palabras_clave`
--
ALTER TABLE `palabras_clave`
  ADD PRIMARY KEY (`id`),
  ADD KEY `subcategoria_id` (`subcategoria_id`);

--
-- Indices de la tabla `subcategorias`
--
ALTER TABLE `subcategorias`
  ADD PRIMARY KEY (`id`),
  ADD KEY `categoria_id` (`categoria_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `categorias`
--
ALTER TABLE `categorias`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `conversaciones`
--
ALTER TABLE `conversaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `palabras_clave`
--
ALTER TABLE `palabras_clave`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;

--
-- AUTO_INCREMENT de la tabla `subcategorias`
--
ALTER TABLE `subcategorias`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `palabras_clave`
--
ALTER TABLE `palabras_clave`
  ADD CONSTRAINT `palabras_clave_ibfk_1` FOREIGN KEY (`subcategoria_id`) REFERENCES `subcategorias` (`id`);

--
-- Filtros para la tabla `subcategorias`
--
ALTER TABLE `subcategorias`
  ADD CONSTRAINT `subcategorias_ibfk_1` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
