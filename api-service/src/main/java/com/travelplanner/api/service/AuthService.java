package com.travelplanner.api.service;

import com.travelplanner.api.dto.AuthResponseDto;
import com.travelplanner.api.dto.LoginRequestDto;
import com.travelplanner.api.dto.SignupRequestDto;
import com.travelplanner.api.dto.UserDto;
import com.travelplanner.api.model.User;
import com.travelplanner.api.repository.UserRepository;
import com.travelplanner.api.security.JwtTokenProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthService(UserRepository userRepository,
                       PasswordEncoder passwordEncoder,
                       JwtTokenProvider jwtTokenProvider) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Transactional
    public AuthResponseDto signup(SignupRequestDto request) {
        if (request.getEmail() == null || request.getEmail().isBlank()) {
            throw new IllegalArgumentException("Email is required");
        }
        if (request.getPassword() == null || request.getPassword().length() < 6) {
            throw new IllegalArgumentException("Password must be at least 6 characters");
        }
        if (request.getName() == null || request.getName().isBlank()) {
            throw new IllegalArgumentException("Name is required");
        }

        String normalizedEmail = request.getEmail().trim().toLowerCase();

        if (userRepository.existsByEmail(normalizedEmail)) {
            throw new IllegalArgumentException("Email is already registered");
        }

        String hashedPassword = passwordEncoder.encode(request.getPassword());
        User user = new User(normalizedEmail, hashedPassword, request.getName().trim());
        user = userRepository.saveAndFlush(user);

        String token = jwtTokenProvider.generateToken(user);
        UserDto userDto = new UserDto(user.getId(), user.getEmail(), user.getName(), user.getCreatedAt());

        return new AuthResponseDto(token, userDto);
    }

    @Transactional(readOnly = true)
    public AuthResponseDto login(LoginRequestDto request) {
        if (request.getEmail() == null || request.getEmail().isBlank() ||
                request.getPassword() == null || request.getPassword().isBlank()) {
            throw new BadCredentialsException("Email and password must be provided");
        }

        String normalizedEmail = request.getEmail().trim().toLowerCase();
        User user = userRepository.findByEmail(normalizedEmail)
                .orElseThrow(() -> new BadCredentialsException("Invalid email or password"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BadCredentialsException("Invalid email or password");
        }

        String token = jwtTokenProvider.generateToken(user);
        UserDto userDto = new UserDto(user.getId(), user.getEmail(), user.getName(), user.getCreatedAt());

        return new AuthResponseDto(token, userDto);
    }
}
